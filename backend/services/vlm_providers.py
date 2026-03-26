"""
VLM Provider Definitions for AURORA SENTINEL
Each provider encapsulates a single AI model integration.
Orchestration logic lives in vlm_service.py.
"""

import os
import sys
import time
import requests
import base64
import io
from abc import ABC, abstractmethod
from PIL import Image

# Optional providers: keep backend functional without them installed/configured.
try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', FutureWarning)
        import google.generativeai as genai
except Exception:
    genai = None

try:
    import ollama
except Exception:
    ollama = None


class VLMProvider(ABC):
    @abstractmethod
    def analyze(self, image, prompt):
        pass


class GeminiProvider(VLMProvider):
    def __init__(self):
        self.available = False
        self.current_model = None

        if genai is None:
            print("[VLM] Gemini disabled (google-generativeai not installed).")
            return

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
        if not api_key:
            print("[VLM] Gemini disabled (no GEMINI_API_KEY/GOOGLE_GENAI_API_KEY).")
            return

        try:
            print(f"[VLM] Configuring Gemini with key: {api_key[:8]}...")
            genai.configure(api_key=api_key)
            self.model_index = 0
            # Rotation helps when a specific model is rate-limited/unavailable.
            self.models = [
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash',
                'gemini-1.5-flash-002',
                'gemini-1.5-pro-latest',
                'gemini-1.5-pro',
            ]
            self.current_model = genai.GenerativeModel(self.models[self.model_index])
            self.available = True
        except Exception as e:
            print(f"[VLM] Gemini disabled (configure failed): {e}")
            self.available = False

    def analyze(self, image, prompt):
        if not self.available or self.current_model is None:
            return "Error: Gemini not configured"
        
        max_retries = len(self.models)
        
        for attempt in range(max_retries):
            model_name = self.models[self.model_index]
            try:
                response = self.current_model.generate_content([prompt, image])
                return response.text
            except Exception as e:
                err_str = str(e).lower()
                print(f"[VLM] Gemini Error on {model_name}: {err_str}")
                
                # Handle Quota / Rate Limits (429)
                if "429" in err_str or "quota" in err_str:
                    print(f"[VLM] Rate limit hit for {model_name}. Rotating to next model...")
                    self.model_index = (self.model_index + 1) % len(self.models)
                    self.current_model = genai.GenerativeModel(self.models[self.model_index])
                    time.sleep(1)
                    continue
                
                # Handle 404 or other model-specific errors
                if "404" in err_str or "503" in err_str:
                    print(f"[VLM] Model {model_name} unavailable. Rotating...")
                    self.model_index = (self.model_index + 1) % len(self.models)
                    self.current_model = genai.GenerativeModel(self.models[self.model_index])
                    continue
                
                return f"Error: {err_str}"
        
        return "Error: All Gemini models exhausted (Rate Limits/Quota reached)."


class OllamaProvider(VLMProvider):
    def __init__(self, model_name=None):
        # Add root directory to path to support config.py import
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        try:
            import config
            self.model_name = getattr(config, "OLLAMA_CLOUD_MODEL", "qwen3-vl:235b-cloud")
        except ImportError:
            self.model_name = "qwen3-vl:235b-cloud"
            
        if model_name:
            self.model_name = model_name

    def analyze(self, image, prompt):
        if ollama is None:
            return "Error: Ollama not installed"

        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            response = ollama.chat(
                model=self.model_name,
                keep_alive=-1,
                messages=[{'role': 'user', 'content': prompt, 'images': [img_bytes]}]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Ollama Error: {e}")
            return f"Error: {e}"


class NemotronProvider:
    """
    Nemotron ColEmbed V2 embedding model for verification.
    This is NOT a generative model - it uses embedding-based similarity scoring.
    """
    def __init__(self):
        self.available = False
        self.model = None
        self.processor = None
        
        if os.getenv("ENABLE_HEAVY_MODELS", "false").lower() != "true":
            print("[VLM] Nemotron disabled (ENABLE_HEAVY_MODELS is not 'true')")
            return
            
        try:
            from transformers import AutoModel, AutoProcessor
            import torch
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            try:
                import config
                model_id = getattr(config, "NEMOTRON_MODEL_ID", "nvidia/nemotron-colembed-vl-4b-v2")
            except ImportError:
                model_id = "nvidia/nemotron-colembed-vl-4b-v2"
                
            print(f"[VLM] Loading Nemotron ({model_id})...")
            self.model = AutoModel.from_pretrained(
                model_id, 
                trust_remote_code=True, 
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            self.processor = AutoProcessor.from_pretrained(
                model_id, 
                trust_remote_code=True
            )
            self.available = True
            print("[VLM] Nemotron loaded successfully")
        except Exception as e:
            print(f"[VLM] Nemotron Load Error: {e}")
            self.available = False

    def forward_images(self, images):
        """Compute image embeddings."""
        if not self.available:
            raise RuntimeError("Nemotron model not available")
        
        try:
            import torch
            inputs = self.processor(images=images, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                embeddings = self.model.get_image_features(**inputs)
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Failed to compute image embeddings: {e}")

    def forward_queries(self, queries):
        """Compute text query embeddings."""
        if not self.available:
            raise RuntimeError("Nemotron model not available")
        
        try:
            import torch
            inputs = self.processor(text=queries, return_tensors="pt", padding=True).to(self.model.device)
            with torch.no_grad():
                embeddings = self.model.get_text_features(**inputs)
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Failed to compute text embeddings: {e}")

    def get_scores(self, image_embeddings, query_embeddings):
        """Compute cosine similarity scores between image and query embeddings."""
        if not self.available:
            raise RuntimeError("Nemotron model not available")
        
        try:
            import torch
            import numpy as np
            
            image_norm = image_embeddings / image_embeddings.norm(dim=-1, keepdim=True)
            query_norm = query_embeddings / query_embeddings.norm(dim=-1, keepdim=True)
            
            scores = torch.matmul(image_norm, query_norm.T)
            return scores.cpu().numpy()
        except Exception as e:
            raise RuntimeError(f"Failed to compute similarity scores: {e}")

    def verify_analysis(self, image, qwen_summary, qwen_scene_type, qwen_risk_score, timeout=3.0):
        """
        Verify Qwen/Ollama analysis using embedding similarity.
        
        Returns:
            Dict with verification_score, verified, category_scores,
            nemotron_scene_type, nemotron_risk_score, agreement,
            recommended_score, confidence, timed_out, latency_ms
        """
        if not self.available:
            raise RuntimeError("Nemotron model not available")
        
        import time
        start_time = time.time()
        
        try:
            import numpy as np
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Nemotron verification exceeded timeout")
            
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))
            
            try:
                # 1. Compute embeddings
                image_embedding = self.forward_images([image])
                summary_embedding = self.forward_queries([qwen_summary])
                
                # 2. Predefined threat category queries
                threat_queries = [
                    "real fight with violence and aggression in public space",
                    "organized sport with protective gear and referee",
                    "normal safe activity with no threats",
                    "suspicious crowd behavior covering people or unknown items"
                ]
                query_embeddings = self.forward_queries(threat_queries)
                
                # 3. Compute similarity scores
                verification_scores = self.get_scores(image_embedding, summary_embedding)
                verification_score = float(verification_scores[0, 0])
                
                category_scores_array = self.get_scores(image_embedding, query_embeddings)
                category_scores_list = category_scores_array[0].tolist()
                
                # 4. Determine Nemotron's classification
                category_map = {
                    0: 'real_fight',
                    1: 'organized_sport',
                    2: 'normal',
                    3: 'suspicious'
                }
                max_idx = int(np.argmax(category_scores_list))
                nemotron_scene_type = category_map[max_idx]
                max_category_score = category_scores_list[max_idx]
                
                # 5. Map similarity to risk score
                risk_map = {
                    'real_fight': (80, 95),
                    'organized_sport': (20, 35),
                    'normal': (10, 25),
                    'suspicious': (60, 75)
                }
                
                if max_category_score > 0.7:
                    risk_range = risk_map[nemotron_scene_type]
                    nemotron_risk_score = int(np.mean(risk_range))
                else:
                    nemotron_risk_score = 50
                
                # 6. Determine agreement and recommendation
                verified = verification_score > 0.6
                agreement = nemotron_scene_type == qwen_scene_type
                
                if verified and agreement:
                    recommended_score = int((qwen_risk_score + nemotron_risk_score) / 2)
                    confidence = 0.9
                elif not verified or not agreement:
                    recommended_score = max(qwen_risk_score, nemotron_risk_score)
                    confidence = 0.5
                else:
                    recommended_score = qwen_risk_score
                    confidence = 0.7
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                return {
                    'verification_score': verification_score,
                    'verified': verified,
                    'category_scores': {
                        'real_fight': float(category_scores_list[0]),
                        'organized_sport': float(category_scores_list[1]),
                        'normal': float(category_scores_list[2]),
                        'suspicious': float(category_scores_list[3])
                    },
                    'nemotron_scene_type': nemotron_scene_type,
                    'nemotron_risk_score': nemotron_risk_score,
                    'agreement': agreement,
                    'recommended_score': recommended_score,
                    'confidence': confidence,
                    'timed_out': False,
                    'latency_ms': latency_ms
                }
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    
        except TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            print(f"[VLM] Nemotron verification timed out after {latency_ms}ms")
            return {
                'verification_score': 0.0,
                'verified': False,
                'category_scores': {
                    'real_fight': 0.0,
                    'organized_sport': 0.0,
                    'normal': 0.0,
                    'suspicious': 0.0
                },
                'nemotron_scene_type': qwen_scene_type,
                'nemotron_risk_score': qwen_risk_score,
                'agreement': True,
                'recommended_score': qwen_risk_score,
                'confidence': 0.6,
                'timed_out': True,
                'latency_ms': latency_ms
            }
        except Exception as e:
            raise RuntimeError(f"Failed to verify analysis: {e}")


def decode_base64_image(image_data):
    """Decode base64 image to PIL Image"""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        return image
    except Exception as e:
        print(f"Failed to decode image: {e}")
        return None
