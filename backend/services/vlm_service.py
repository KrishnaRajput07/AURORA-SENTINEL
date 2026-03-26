"""
VLM Service — Simplified Single-Model + Fallback Orchestrator

Architecture:
  Primary   → Ollama (Qwen3-VL 235B cloud)
  Backup    → Gemini (cloud API)
  Verifier  → Nemotron (embedding-based, optional)

No fusion engine, no weighted multi-provider averaging.
Just use the best available single response.
"""

import os
import sys
import time
import base64
import io
import re
from PIL import Image

# Import providers from separated module
from backend.services.vlm_providers import (
    OllamaProvider,
    GeminiProvider,
    NemotronProvider,
    decode_base64_image,
)

# Optional ollama import for answer_question
try:
    import ollama as ollama_lib
except Exception:
    ollama_lib = None

# Load config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    import config
    SPORT_RISK_CAP = getattr(config, "SPORT_RISK_CAP", 15)
    PRELOAD_LOCAL_MODELS = getattr(config, "PRELOAD_LOCAL_MODELS", False)
except ImportError:
    SPORT_RISK_CAP = 15
    PRELOAD_LOCAL_MODELS = False


class VLMService:
    """
    Simplified VLM orchestrator.
    Primary: Ollama (Qwen3-VL 235B) → Backup: Gemini → Fallback: ML-only description.
    Nemotron kept as optional verifier (not in the main analysis chain).
    """

    def __init__(self):
        self.ollama = OllamaProvider()
        self.gemini = GeminiProvider()

        # Nemotron: optional verification model (only if heavy models enabled)
        if PRELOAD_LOCAL_MODELS:
            self.nemotron = NemotronProvider()
            print("[VLM] Nemotron pre-loaded for verification.")
        else:
            class _DummyNemotron:
                available = False
            self.nemotron = _DummyNemotron()
            print("[VLM] Nemotron skipped (PRELOAD_LOCAL_MODELS=False).")

        self.provider_name = "ollama"  # Current active provider label
        print("VLM Service Initialized (Ollama Primary + Gemini Backup)")

    # ------------------------------------------------------------------
    # Core: Scene Analysis (used by offline_processor + stream_vlm)
    # ------------------------------------------------------------------
    def analyze_scene(self, frame_pil, prompt=None, risk_score=0):
        """
        Single-model analysis with sequential fallback.
        Returns: { provider, description, latency, risk_score, ensemble_size }
        """
        start = time.time()

        # --- 1. PROMPT REFINEMENT ---
        numeric_risk = 0
        risk_str = str(risk_score).lower()
        if isinstance(risk_score, (int, float)):
            numeric_risk = risk_score
        elif isinstance(risk_score, (list, dict)):
            if any(x in risk_str for x in ["arm_raise", "aggression", "shove"]):
                numeric_risk = 85
            else:
                numeric_risk = 40

        if not prompt:
            if "causal_fall" in risk_str:
                prompt = "EXAMINE: A person is on the ground. Is this an accidental slip/fall, or did the other person push/shove them? Analyze the interaction logic."
            elif numeric_risk >= 85:
                prompt = "CRITICAL: Describe the violence/weapon. Differentiate if it's a sport (boxing) or a real threat."
            elif numeric_risk >= 40:
                prompt = "AUDIT: Analyze behavior. Is this a threat, a prank, or organized sport?"
            else:
                prompt = "SANITY CHECK: Verify if this scene is truly safe. Look for hidden threats."

        # --- 2. TRY OLLAMA (Primary — Qwen3-VL 235B) ---
        try:
            print(f"[VLM] Trying Ollama ({self.ollama.model_name})...")
            result = self.ollama.analyze(frame_pil, prompt)
            if result and "Error" not in result:
                latency = time.time() - start
                description = result.strip()
                suggested_risk = self._extract_risk_from_text(description, numeric_risk)
                print(f"[VLM] Ollama completed in {latency:.2f}s")
                self.provider_name = "ollama"
                return {
                    "provider": "ollama",
                    "description": description,
                    "latency": round(latency, 2),
                    "risk_score": suggested_risk,
                    "ensemble_size": 1
                }
            else:
                print(f"[VLM] Ollama returned error: {result}")
        except Exception as e:
            print(f"[VLM] Ollama failed: {e}")

        # --- 3. TRY GEMINI (Backup — Cloud API) ---
        if getattr(self.gemini, "available", False):
            try:
                print("[VLM] Trying Gemini API (backup)...")
                result = self.gemini.analyze(frame_pil, prompt)
                if result and "Error" not in result:
                    latency = time.time() - start
                    description = result.strip()
                    suggested_risk = self._extract_risk_from_text(description, numeric_risk)
                    print(f"[VLM] Gemini completed in {latency:.2f}s")
                    self.provider_name = "gemini"
                    return {
                        "provider": "gemini",
                        "description": description,
                        "latency": round(latency, 2),
                        "risk_score": suggested_risk,
                        "ensemble_size": 1
                    }
                else:
                    print(f"[VLM] Gemini returned error: {result}")
            except Exception as e:
                print(f"[VLM] Gemini failed: {e}")

        # --- 4. FALLBACK (No providers available) ---
        latency = time.time() - start
        self.provider_name = "none"
        return {
            "provider": "none",
            "description": "No VLM providers available. ML-only analysis active.",
            "latency": round(latency, 2),
            "risk_score": float(numeric_risk) if isinstance(numeric_risk, (int, float)) else 0,
            "ensemble_size": 0
        }

    # ------------------------------------------------------------------
    # Chat Q&A (used by intelligence.py /chat endpoint)
    # ------------------------------------------------------------------
    async def answer_question(self, image_data, question):
        """
        Conversational Q&A about images.
        Priority: Ollama (Qwen3-VL, free) → Gemini (cloud backup).
        """
        try:
            # Decode image
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # 1. Try Ollama (Primary — FREE and local/cloud)
            if ollama_lib is not None:
                try:
                    chat_model = self.ollama.model_name
                    print(f"[VLM-QA] Using Ollama ({chat_model}) for question: {question[:50]}...")

                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='JPEG')
                    img_bytes = img_byte_arr.getvalue()

                    response = ollama_lib.chat(
                        model=chat_model,
                        messages=[{
                            'role': 'user',
                            'content': f"{question}\n\nProvide a concise, direct answer.",
                            'images': [img_bytes]
                        }]
                    )

                    answer = response['message']['content']
                    print(f"[VLM-QA] Ollama response: {answer[:100]}...")

                    return {
                        'answer': answer,
                        'confidence': 0.85,
                        'provider': 'ollama'
                    }
                except Exception as e:
                    print(f"[VLM-QA] Ollama failed: {e}")

            # 2. Try Gemini (Backup — Cloud API)
            if getattr(self.gemini, "available", False):
                try:
                    print("[VLM-QA] Using Gemini for question...")
                    result = self.gemini.analyze(image, question)

                    if result and "Error" not in result:
                        return {
                            'answer': result,
                            'confidence': 0.85,
                            'provider': 'gemini'
                        }
                except Exception as e:
                    print(f"[VLM-QA] Gemini failed: {e}")

            # Fallback
            return {
                'answer': 'Sorry, I could not analyze the image. Please make sure Ollama is running.',
                'confidence': 0.0,
                'provider': 'none'
            }

        except Exception as e:
            print(f"[VLM-QA] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'answer': f'Error processing question: {str(e)}',
                'confidence': 0.0,
                'provider': 'error'
            }

    # ------------------------------------------------------------------
    # Internal: Extract risk level from VLM text output
    # ------------------------------------------------------------------
    def _extract_risk_from_text(self, description, base_risk):
        """
        Extract a risk score from VLM description text using keyword analysis.
        Applies sport/boxing safety cap when appropriate.
        """
        lower_desc = description.lower()

        threat_keywords = {
            "fight": 85, "fighting": 85, "punching": 85, "brawl": 90,
            "shoving": 65, "aggressive": 65, "confrontation": 60,
            "gun": 95, "firearm": 95, "weapon": 85, "knife": 85,
            "robbery": 90, "theft": 70, "intrusion": 75, "blood": 85
        }

        risk = base_risk
        for keyword, score in threat_keywords.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', lower_desc):
                risk = max(risk, score)

        # Sport/boxing safety cap
        sport_indicators = ["boxing", "sparring", "referee", "boxing ring", "boxing gloves"]
        danger_indicators = ["street fight", "unauthorized", "assault", "ambush"]

        if any(s in lower_desc for s in sport_indicators):
            if all(d not in lower_desc for d in danger_indicators):
                risk = min(risk, SPORT_RISK_CAP)

        return risk


# Singleton
vlm_service = VLMService()
