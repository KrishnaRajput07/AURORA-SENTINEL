"""
VLM Service - Simplified Single-Model + Fallback Orchestrator.

Architecture:
  Primary   -> Ollama (Qwen3-VL)
  Backup    -> Gemini
  Verifier  -> Nemotron (lazy-load capable)
"""

import base64
import io
import os
import re
import sys
import time
from typing import List, Optional

from PIL import Image

from backend.services.vlm_providers import GeminiProvider, NemotronProvider, OllamaProvider

try:
    import ollama as ollama_lib
except Exception:
    ollama_lib = None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    import config

    SPORT_RISK_CAP = getattr(config, "SPORT_RISK_CAP", 15)
    PRELOAD_LOCAL_MODELS = getattr(config, "PRELOAD_LOCAL_MODELS", False)
    ENABLE_NEMOTRON_VERIFICATION = getattr(config, "ENABLE_NEMOTRON_VERIFICATION", True)
    NEMOTRON_TIMEOUT = getattr(config, "NEMOTRON_TIMEOUT", 3.0)
except Exception:
    SPORT_RISK_CAP = 15
    PRELOAD_LOCAL_MODELS = False
    ENABLE_NEMOTRON_VERIFICATION = True
    NEMOTRON_TIMEOUT = 3.0


class VLMService:
    """
    Simplified VLM orchestrator.
    Primary: Ollama -> Backup: Gemini -> Fallback: ML-only description.
    Nemotron verification is optional and can be lazy-loaded.
    """

    def __init__(self):
        self.ollama = OllamaProvider()
        self.gemini = GeminiProvider()
        self.provider_name = "ollama"

        self._nemotron = None
        if PRELOAD_LOCAL_MODELS:
            self._nemotron = NemotronProvider()
            print("[VLM] Nemotron pre-loaded for verification.")
        else:
            print("[VLM] Nemotron lazy-load mode enabled.")

        print("VLM Service Initialized (Ollama Primary + Gemini Backup)")

    def _get_nemotron(self):
        if self._nemotron is None:
            try:
                self._nemotron = NemotronProvider()
            except Exception as e:
                print(f"[VLM] Nemotron lazy load failed: {e}")
                self._nemotron = None
        return self._nemotron

    def _infer_scene_type(self, description: str) -> str:
        text = (description or "").lower()
        if any(k in text for k in ["boxing", "sparring", "referee"]):
            return "organized_sport"
        if any(k in text for k in ["fight", "assault", "punch", "brawl"]):
            return "real_fight"
        if any(k in text for k in ["suspicious", "covering face", "running"]):
            return "suspicious"
        return "normal"

    def _apply_nemotron_verification(self, frame_pil, description: str, risk_score: float):
        if not ENABLE_NEMOTRON_VERIFICATION:
            return risk_score, self._infer_scene_type(description), None

        nemotron = self._get_nemotron()
        if nemotron is None or not getattr(nemotron, "available", False):
            return risk_score, self._infer_scene_type(description), None

        scene_type = self._infer_scene_type(description)
        try:
            verification = nemotron.verify_analysis(
                frame_pil,
                description,
                scene_type,
                int(risk_score),
                timeout=NEMOTRON_TIMEOUT,
            )
            recommended = float(verification.get("recommended_score", risk_score))
            recommended = max(0.0, min(100.0, recommended))
            scene_type = verification.get("nemotron_scene_type", scene_type)
            return recommended, scene_type, verification
        except Exception as e:
            print(f"[VLM] Nemotron verification failed: {e}")
            return risk_score, scene_type, None

    def analyze_scene(self, frame_pil, prompt=None, risk_score=0):
        """
        Single-model analysis with sequential fallback.
        Returns: { provider, description, latency, risk_score, ensemble_size, scene_type? }
        """
        start = time.time()

        numeric_risk = 0
        risk_str = str(risk_score).lower()
        if isinstance(risk_score, (int, float)):
            numeric_risk = float(risk_score)
        elif isinstance(risk_score, (list, dict)):
            if any(x in risk_str for x in ["arm_raise", "aggression", "shove"]):
                numeric_risk = 85
            else:
                numeric_risk = 40

        if not prompt:
            # Use enhanced contextual prompts
            try:
                from backend.services.enhanced_vlm_prompts import build_contextual_prompts
                prompt = build_contextual_prompts(numeric_risk, risk_str)
            except ImportError:
                # Fallback to original prompts
                if "causal_fall" in risk_str:
                    prompt = (
                        "EXAMINE: A person is on the ground. Is this an accidental slip/fall, "
                        "or did the other person push/shove them? Analyze the interaction logic."
                    )
                elif numeric_risk >= 85:
                    prompt = "CRITICAL: Describe the violence/weapon. Differentiate sport from real threat."
                elif numeric_risk >= 40:
                    prompt = "AUDIT: Analyze behavior. Is this a threat, prank, or organized sport?"
                else:
                    prompt = "SANITY CHECK: Verify if this scene is safe. Look for hidden threats."

        providers = [
            ("ollama", self.ollama.analyze),
            ("gemini", self.gemini.analyze if getattr(self.gemini, "available", False) else None),
        ]

        for provider_name, fn in providers:
            if fn is None:
                print(f"[VLM] ⚠️ {provider_name} provider is None (not configured), skipping...")
                continue
            try:
                print(f"[VLM] Trying {provider_name}...")
                result = fn(frame_pil, prompt)
                if result and "Error" not in result:
                    latency = time.time() - start
                    description = result.strip()
                    suggested_risk = self._extract_risk_from_text(description, numeric_risk)
                    adjusted_risk, scene_type, nemotron_verification = self._apply_nemotron_verification(
                        frame_pil, description, suggested_risk
                    )

                    self.provider_name = provider_name
                    payload = {
                        "provider": provider_name,
                        "description": description,
                        "latency": round(latency, 2),
                        "risk_score": round(float(adjusted_risk), 2),
                        "ensemble_size": 1,
                        "scene_type": scene_type,
                    }
                    if nemotron_verification:
                        payload["nemotron_verification"] = nemotron_verification
                    return payload
                else:
                    # EXPLICIT FALLBACK LOGGING
                    print(f"[VLM] ❌ {provider_name} returned error: {result}")
                    print(f"[VLM] ⚠️ FALLBACK: Switching to next provider...")
            except Exception as e:
                print(f"[VLM] ❌ {provider_name} failed with exception: {e}")
                print(f"[VLM] ⚠️ FALLBACK: Switching to next provider...")

        latency = time.time() - start
        self.provider_name = "none"
        # ALL PROVIDERS FAILED - EXPLICIT LOG
        print(f"[VLM] 🚨 ALL PROVIDERS FAILED! Falling back to ML-only analysis.")
        print(f"[VLM] 🚨 This means Ollama cloud model may not be reachable. Check your OLLAMA_HOST or API key.")
        return {
            "provider": "none",
            "description": "No VLM providers available. ML-only analysis active.",
            "latency": round(latency, 2),
            "risk_score": float(numeric_risk),
            "ensemble_size": 0,
            "scene_type": "normal",
        }

    async def answer_question(self, image_data, question):
        """
        Conversational Q&A about images.
        Priority: Ollama -> Gemini.
        """
        try:
            if "," in image_data:
                image_data = image_data.split(",")[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            if ollama_lib is not None:
                try:
                    chat_model = self.ollama.model_name
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format="JPEG")
                    img_bytes = img_byte_arr.getvalue()

                    response = ollama_lib.chat(
                        model=chat_model,
                        messages=[
                            {
                                "role": "user",
                                "content": f"{question}\n\nProvide a concise, direct answer.",
                                "images": [img_bytes],
                            }
                        ],
                    )

                    answer = response["message"]["content"]
                    return {
                        "answer": answer,
                        "confidence": 0.85,
                        "provider": "ollama",
                    }
                except Exception as e:
                    print(f"[VLM-QA] Ollama failed: {e}")

            if getattr(self.gemini, "available", False):
                try:
                    result = self.gemini.analyze(image, question)
                    if result and "Error" not in result:
                        return {
                            "answer": result,
                            "confidence": 0.8,
                            "provider": "gemini",
                        }
                except Exception as e:
                    print(f"[VLM-QA] Gemini failed: {e}")

            return {
                "answer": "Sorry, I could not analyze the image. Please make sure Ollama is running.",
                "confidence": 0.0,
                "provider": "none",
            }
        except Exception as e:
            print(f"[VLM-QA] Error: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "confidence": 0.0,
                "provider": "error",
            }

    def answer_with_context(
        self,
        question: str,
        context_blocks: List[str],
        history: Optional[List[dict]] = None,
    ):
        """
        Text-only context QA used by timeline-aware chat and video summary generation.
        """
        context = "\n".join([c for c in context_blocks if c]).strip()
        if not context:
            return {
                "answer": "No timeline context is available yet.",
                "confidence": 0.2,
                "provider": "fallback",
            }

        history_text = ""
        if history:
            parts = []
            for turn in history[-6:]:
                role = str(turn.get("role", "user"))
                content = str(turn.get("content", ""))
                if content:
                    parts.append(f"{role}: {content}")
            if parts:
                history_text = "\nConversation History:\n" + "\n".join(parts)

        prompt = (
            "You are a surveillance analyst. Answer based only on the supplied timeline context. "
            "If uncertain, say so briefly.\n\n"
            f"Question: {question}\n\n"
            f"Timeline Context:\n{context}\n"
            f"{history_text}\n\n"
            "Return a concise answer."
        )

        if ollama_lib is not None:
            try:
                response = ollama_lib.chat(
                    model=self.ollama.model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                answer = response["message"]["content"]
                return {"answer": answer, "confidence": 0.78, "provider": "ollama_text"}
            except Exception as e:
                print(f"[VLM-TEXT] Ollama text QA failed: {e}")

        # Fallback deterministic summary
        first_lines = [line.strip("- ").strip() for line in context.splitlines() if line.strip()][:3]
        fallback_answer = " ".join(first_lines)
        return {
            "answer": fallback_answer or "No useful timeline details available.",
            "confidence": 0.45,
            "provider": "fallback",
        }

    def summarize_events(self, filename: str, events: List[dict]):
        """
        Generate a video-level executive summary from event descriptions.
        """
        if not events:
            return {
                "summary": "No significant events were found in this video.",
                "provider": "fallback",
                "confidence": 0.2,
            }

        context_blocks = []
        for evt in events[:20]:
            ts = round(float(evt.get("timestamp", 0) or 0), 1)
            sev = evt.get("severity", "low")
            desc = (evt.get("description", "") or "").strip()
            if desc:
                context_blocks.append(f"- [{ts}s][{sev}] {desc}")

        response = self.answer_with_context(
            question=f"Provide an executive summary for video '{filename}'.",
            context_blocks=context_blocks,
            history=None,
        )
        return {
            "summary": response.get("answer", ""),
            "provider": response.get("provider", "fallback"),
            "confidence": float(response.get("confidence", 0.5)),
        }

    @staticmethod
    def _is_negated(text, keyword, window=6):
        """Return True if `keyword` is preceded by a negation word within `window` words."""
        negations = {'not', 'no', 'never', 'without', "isn't", "aren't", "doesn't",
                     "don't", "neither", "nor", 'non', 'nothing', 'nobody'}
        pattern = r'\b' + re.escape(keyword) + r'\b'
        for m in re.finditer(pattern, text):
            preceding = text[:m.start()].split()[-window:]
            if any(neg in preceding for neg in negations):
                return True
        return False

    def _extract_risk_from_text(self, description, base_risk):
        """
        Extract a risk score from VLM description text using keyword analysis.
        Applies negation awareness and sport/boxing safety cap.
        """
        lower_desc = (description or "").lower()

        threat_keywords = {
            "fight": 85,
            "fighting": 85,
            "punching": 85,
            "brawl": 90,
            "shoving": 65,
            "aggressive": 65,
            "confrontation": 60,
            "gun": 95,
            "firearm": 95,
            "weapon": 85,
            "knife": 85,
            "robbery": 90,
            "theft": 70,
            "intrusion": 75,
            "blood": 85,
        }

        risk = float(base_risk)
        for keyword, score in threat_keywords.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", lower_desc):
                if not self._is_negated(lower_desc, keyword):
                    risk = max(risk, score)

        # Sport/prank override — only if NOT negated
        sport_indicators = ["boxing", "sparring", "referee", "boxing ring", "boxing gloves"]
        danger_indicators = ["street fight", "unauthorized", "assault", "ambush"]
        is_sport = any(
            kw in lower_desc and not self._is_negated(lower_desc, kw)
            for kw in sport_indicators
        )
        is_real_fight = any(
            kw in lower_desc and not self._is_negated(lower_desc, kw)
            for kw in danger_indicators
        )
        if is_sport and not is_real_fight:
            risk = min(risk, SPORT_RISK_CAP)

        return risk


vlm_service = VLMService()
