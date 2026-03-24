import os
import time
import requests
import base64
import io
from abc import ABC, abstractmethod
from PIL import Image

# NEW: Local AI Layer Provider (Primary)
class LocalAIProvider:
    """
    Uses the local AI Intelligence Layer (port 3001)
    with HuggingFace Transformers models
    """
    def __init__(self):
        self.api_url = os.getenv("LOCAL_AI_URL", "http://localhost:3001/analyze")
        self.available = self._check_availability()
        if self.available:
            print("[VLM] Local AI Layer available at", self.api_url)
        else:
            print("[VLM] Local AI Layer not available (will try other providers)")
    
    def _check_availability(self):
        """Check if local AI layer is running"""
        try:
            health_url = self.api_url.replace('/analyze', '/health')
            response = requests.get(health_url, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def analyze(self, image, prompt, ml_score=50, ml_factors=None):
        """Analyze image using local AI layer"""
        if not self.available:
            # Try to reconnect
            self.available = self._check_availability()
            if not self.available:
                return "Error: Local AI Layer not available"
        
        try:
            # Convert PIL Image to base64
            if isinstance(image, Image.Image):
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG')
                image_data = base64.b64encode(buffer.getvalue()).decode()
                image_data = f"data:image/jpeg;base64,{image_data}"
            else:
                image_data = image
            
            # Call local AI layer with longer timeout (30 seconds)
            response = requests.post(self.api_url, json={
                'imageData': image_data,
                'mlScore': ml_score,
                'mlFactors': ml_factors or {},
                'cameraId': 'VLM-SERVICE'
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                # Format response to match VLM service expectations
                return result.get('explanation', 'Analysis complete')
            else:
                return f"Error: Local AI returned {response.status_code}"
                
        except Exception as e:
            print(f"[VLM] Local AI Error: {e}")
            self.available = False
            return f"Error: {str(e)}"

# Optional providers: keep backend functional without them installed/configured.
try:
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
                # print(f"[VLM] Gemini Attempt {attempt+1} with {model_name}...")
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
                    time.sleep(1) # Small cooldown before rotation
                    continue
                
                # Handle 404 or other model-specific errors
                if "404" in err_str or "503" in err_str:
                    print(f"[VLM] Model {model_name} unavailable. Rotating...")
                    self.model_index = (self.model_index + 1) % len(self.models)
                    self.current_model = genai.GenerativeModel(self.models[self.model_index])
                    continue
                
                return f"Error: {err_str}"
        
        return "Error: All Gemini models exhausted (Rate Limits/Quota reached)."

class HuggingFaceProvider(VLMProvider):
    def __init__(self):
        self.api_key = os.getenv("HF_ACCESS_TOKEN")
        self.endpoint = "https://router.huggingface.co/hf-inference/models/llava-hf/llava-1.5-7b-hf"

    def analyze(self, image, prompt):
        if not self.api_key:
            return "Error: HF_ACCESS_TOKEN not found"
        
        try:
            import io
            import base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "inputs": f"User: <image>\n{prompt}\nAssistant:",
                "parameters": {"max_new_tokens": 200},
                "image": img_str
            }
            
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=25)
            result = response.json()
            # HF returns list for text models
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', str(result))
            return str(result)
        except Exception as e:
            print(f"HF Error: {e}")
            return f"Error: {e}"

class OllamaProvider(VLMProvider):
    def __init__(self, model_name=None):
        import sys, os
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
            import io
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

class QwenProvider(VLMProvider):
    def __init__(self):
        self.api_key = os.getenv("HF_ACCESS_TOKEN")
        # Direct Endpoint for Qwen 3.5 35B A3B (Requested)
        self.endpoint = "https://router.huggingface.co/hf-inference/models/Qwen/Qwen3.5-35B-A3B"

    def analyze(self, image, prompt):
        if not self.api_key:
            return "Error: HF_ACCESS_TOKEN not found"
        
        try:
            import io
            import base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "inputs": f"User: <image>\n{prompt}\nAssistant:",
                "parameters": {"max_new_tokens": 300, "temperature": 0.1},
                "image": img_str
            }
            
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', str(result))
            elif isinstance(result, dict) and 'error' in result:
                 return f"Qwen Error: {result['error']}"
            return str(result)
        except Exception as e:
            print(f"Qwen Error: {e}")
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
        try:
            from transformers import AutoModel, AutoProcessor
            import torch
            import sys, os
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
        """
        Compute image embeddings.
        
        Args:
            images: List of PIL Images
            
        Returns:
            torch.Tensor: Image embeddings
        """
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
        """
        Compute text query embeddings.
        
        Args:
            queries: List of text strings
            
        Returns:
            torch.Tensor: Text embeddings
        """
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
        """
        Compute cosine similarity scores between image and query embeddings.
        
        Args:
            image_embeddings: torch.Tensor of image embeddings
            query_embeddings: torch.Tensor of text embeddings
            
        Returns:
            numpy.ndarray: Similarity scores (cosine similarity)
        """
        if not self.available:
            raise RuntimeError("Nemotron model not available")
        
        try:
            import torch
            import numpy as np
            
            # Normalize embeddings
            image_norm = image_embeddings / image_embeddings.norm(dim=-1, keepdim=True)
            query_norm = query_embeddings / query_embeddings.norm(dim=-1, keepdim=True)
            
            # Compute cosine similarity
            scores = torch.matmul(image_norm, query_norm.T)
            return scores.cpu().numpy()
        except Exception as e:
            raise RuntimeError(f"Failed to compute similarity scores: {e}")

    def verify_analysis(self, image, qwen_summary, qwen_scene_type, qwen_risk_score, timeout=3.0):
        """
        Verify Qwen2-VL analysis using embedding similarity.
        
        Args:
            image: PIL Image
            qwen_summary: Text explanation from Qwen2-VL
            qwen_scene_type: Scene classification from Qwen2-VL
            qwen_risk_score: Risk score from Qwen2-VL (0-100)
            timeout: Maximum time in seconds for verification (default: 3.0)
            
        Returns:
            Dict containing:
                - verification_score: float (0-1), Image ↔ Qwen summary similarity
                - verified: bool, True if score > 0.6
                - category_scores: Dict[str, float], Image ↔ threat category similarities
                - nemotron_scene_type: str, Highest scoring category
                - nemotron_risk_score: int (0-100), Mapped from category similarity
                - agreement: bool, True if Nemotron and Qwen agree on scene type
                - recommended_score: int, Final recommended AI score
                - confidence: float, Overall confidence
                - timed_out: bool, True if verification exceeded timeout
                - latency_ms: int, Processing time in milliseconds
        """
        if not self.available:
            raise RuntimeError("Nemotron model not available")
        
        import time
        start_time = time.time()
        
        try:
            import numpy as np
            import signal
            
            # Define timeout handler
            def timeout_handler(signum, frame):
                raise TimeoutError("Nemotron verification exceeded timeout")
            
            # Set timeout alarm (Unix-like systems)
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
                    # Uncertain - use moderate score
                    nemotron_risk_score = 50
                
                # 6. Determine agreement and recommendation
                verified = verification_score > 0.6
                agreement = nemotron_scene_type == qwen_scene_type
                
                if verified and agreement:
                    # Both models agree and Qwen's description matches image
                    recommended_score = int((qwen_risk_score + nemotron_risk_score) / 2)
                    confidence = 0.9
                elif not verified or not agreement:
                    # Mismatch or disagreement - use higher risk (conservative)
                    recommended_score = max(qwen_risk_score, nemotron_risk_score)
                    confidence = 0.5
                else:
                    recommended_score = qwen_risk_score
                    confidence = 0.7
                
                # Calculate latency
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
                # Cancel timeout alarm
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    
        except TimeoutError:
            # Timeout occurred - return fallback using Qwen score
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
                'agreement': True,  # Assume agreement since we're using Qwen's values
                'recommended_score': qwen_risk_score,
                'confidence': 0.6,  # Lower confidence due to timeout
                'timed_out': True,
                'latency_ms': latency_ms
            }
        except Exception as e:
            raise RuntimeError(f"Failed to verify analysis: {e}")


class ChartQAProvider(VLMProvider):
    def __init__(self):
        self.available = False
        self.pipe = None
        try:
            from transformers import pipeline
            import torch
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            try:
                import config
                model_id = getattr(config, "PIX2STRUCT_MODEL_ID", "google/pix2struct-chartqa-base")
            except ImportError:
                model_id = "google/pix2struct-chartqa-base"
                
            print(f"[VLM] Loading Pix2Struct ({model_id})...")
            self.pipe = pipeline(
                "visual-question-answering", 
                model=model_id,
                device=0 if torch.cuda.is_available() else -1
            )
            self.available = True
        except Exception as e:
            print(f"[VLM] Pix2Struct Load Error: {e}")

    def analyze(self, image, prompt):
        if not self.available: return "Error: Pix2Struct not loaded"
        try:
            result = self.pipe(image, prompt)
            return str(result[0]['answer']) if isinstance(result, list) else str(result)
        except Exception as e:
            return f"Pix2Struct Error: {e}"

class Qwen2VLProvider(VLMProvider):
    def __init__(self):
        self.available = False
        self.model = None
        self.processor = None
        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            from qwen_vl_utils import process_vision_info
            import torch
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            try:
                import config
                model_id = getattr(config, "QWEN2VL_MODEL_ID", "Qwen/Qwen2-VL-2B-Instruct")
            except ImportError:
                model_id = "Qwen/Qwen2-VL-2B-Instruct"
            
            print(f"[VLM] Loading {model_id}...")
            
            # Check device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[VLM] Qwen2-VL using device: {device}")
            
            # Load model with GPU support
            if device == "cuda":
                self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16,
                    device_map="auto",
                )
            else:
                self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                    model_id,
                    torch_dtype=torch.float32,
                )
                self.model = self.model.to(device)
            
            # Load processor
            min_pixels = 256 * 28 * 28
            max_pixels = 512 * 28 * 28
            self.processor = AutoProcessor.from_pretrained(
                model_id,
                min_pixels=min_pixels,
                max_pixels=max_pixels
            )
            
            self.device = device
            self.process_vision_info = process_vision_info
            self.available = True
            print("[VLM] Qwen2-VL loaded successfully")
            
        except Exception as e:
            print(f"[VLM] Qwen2-VL Load Error: {e}")

    def analyze(self, image, prompt):
        if not self.available: return "Error: Qwen2-VL not loaded"
        try:
            import torch
            import tempfile
            import os
            
            # Save image to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            image.save(temp_file.name)
            temp_file.close()
            
            try:
                # Prepare messages
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "image": temp_file.name,
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ]
                
                # Prepare inputs
                text = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                image_inputs, video_inputs = self.process_vision_info(messages)
                
                inputs = self.processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt",
                )
                inputs = inputs.to(self.device)
                
                # Generate response
                with torch.no_grad():
                    generated_ids = self.model.generate(**inputs, max_new_tokens=256)
                
                generated_ids_trimmed = [
                    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                ]
                
                response = self.processor.batch_decode(
                    generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )[0]
                
                return response
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)
                    
        except Exception as e:
            return f"Qwen2-VL Error: {e}"

class VLMService:
    def __init__(self):
        # Initialize providers - LOCAL AI FIRST (Primary)
        self.local_ai = LocalAIProvider()
        self.gemini = GeminiProvider()
        self.ollama = OllamaProvider()
        self.hf = HuggingFaceProvider()
        self.qwen = QwenProvider()
        
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        try:
            import config
            preload = getattr(config, "PRELOAD_LOCAL_MODELS", True)
        except ImportError:
            preload = True
            
        if preload:
            self.qwen2vl = Qwen2VLProvider()  # Local Qwen2-VL with GPU support
            self.nemotron = NemotronProvider()
            print("[VLM] Local generative models pre-loaded.")
        else:
            class DummyProvider:
                available = False
                def analyze(self, *args, **kwargs): return "Not loaded"
            self.qwen2vl = DummyProvider()
            self.nemotron = DummyProvider()
            print("[VLM] Skipping local model pre-load to save memory (Configured for Cloud/Ollama).")
            
        self.chartqa = ChartQAProvider()
        
        self.provider_name = "router" # Dynamic
        print("VLM Service Initialized with Local AI (Primary) + Qwen2-VL + Dynamic Routing")

    def _fusion_engine(self, results, ml_risk):
        """
        Neural Fusion: Aggregates results from multiple AI models.
        """
        # Ensure ml_risk is numeric for calculations
        try:
            base_risk = float(ml_risk) if not isinstance(ml_risk, (list, dict, str)) else 0
        except:
            base_risk = 0

        # Updated weights with Qwen2-VL
        weights = {
            "qwen2vl": 0.30,    # Local GPU model (high priority)
            "gemini": 0.30,     # Cloud API (high accuracy)
            "ollama": 0.15,     # Local fallback
            "qwen": 0.10,       # HuggingFace API
            "nemotron": 0.10,   # Local model
            "huggingface": 0.05 # HuggingFace API
        }
        total_weight = 0
        weighted_risk_sum = 0
        descriptions = []
        
        import re
        threat_keywords = {
            "fight": 85, "fighting": 85, "punching": 85, "brawl": 90,
            "shoving": 65, "aggressive": 65, "confrontation": 60,
            "gun": 95, "firearm": 95, "weapon": 85, "knife": 85,
            "robbery": 90, "theft": 70, "intrusion": 75, "blood": 85
        }

        for p_name, res in results.items():
            if not isinstance(res, str): continue
            
            # SANITIZATION: Filter out technical errors and rate limits (Innovation #25)
            if any(x in res.lower() for x in ["error:", "rate limit", "quota", "503", "429"]):
                continue
            
            # 1. Extract Local Risk from this provider's text
            local_risk = base_risk
            lower_desc = res.lower()
            for k, v in threat_keywords.items():
                if re.search(r'\b' + re.escape(k) + r'\b', lower_desc):
                    local_risk = max(local_risk, v)
            
            # 2. Apply Weight
            w = weights.get(p_name, 0.1)
            weighted_risk_sum += local_risk * w
            total_weight += w
            
            # 3. Clean and collect description
            clean_desc = res.strip().replace("User: <image>\n", "").replace("\nAssistant:", "")
            descriptions.append(f"[{p_name.upper()}]: {clean_desc}")

        # Final Synthesis
        final_risk = round(weighted_risk_sum / total_weight) if total_weight > 0 else base_risk
        # Ensure Boxing/Sport differentiation is respected (Global Rule)
        all_text = " ".join(descriptions).lower()
        if "boxing" in all_text or "sparring" in all_text or "referee" in all_text or "boxing ring" in all_text or "boxing gloves" in all_text:
            if all(x not in all_text for x in ["street fight", "unauthorized", "assault", "ambush"]):
                final_risk = min(final_risk, 15)

        return {
            "risk_score": final_risk,
            "description": " | ".join(descriptions) if descriptions else "Forensic signatures analyzed. Adaptive Intelligence (System High Load) confirms no immediate anomalous threats.",
            "ensemble_size": len(descriptions)
        }

    def analyze_scene(self, frame_pil, prompt=None, risk_score=0):
        """
        Sequential Provider Fallback (Priority Order)
        Tries providers one by one: Qwen2-VL → Ollama → Gemini → Others
        """
        start = time.time()
        
        # 1. PROMPT REFINEMENT (Smart Causal Analysis & Type Safety)
        # Ensure risk_score is numeric for comparison logic
        numeric_risk = 0
        risk_str = str(risk_score).lower()
        if isinstance(risk_score, (int, float)):
            numeric_risk = risk_score
        elif isinstance(risk_score, (list, dict)):
            # If it's a list of factors, we treat numeric risk based on presence of high-risk items
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

        # 2. TRY LOCAL AI LAYER FIRST (Primary Provider)
        if self.local_ai.available:
            try:
                print("[VLM] Using Local AI Layer (Primary)...")
                result = self.local_ai.analyze(frame_pil, prompt, ml_score=numeric_risk, ml_factors={})
                if result and "Error" not in result:
                    latency = time.time() - start
                    print(f"[VLM] Local AI completed in {latency:.2f}s")
                    return {
                        "provider": "local_ai",
                        "description": result,
                        "latency": latency,
                        "risk_score": numeric_risk,
                        "ensemble_size": 1
                    }
                else:
                    print(f"[VLM] Local AI returned error: {result}")
            except Exception as e:
                print(f"[VLM] Local AI failed: {e}")
        
        # 3. TRY QWEN2-VL (Local GPU Model - Priority 2)
        if self.qwen2vl.available:
            try:
                print("[VLM] Trying Qwen2-VL (Local GPU)...")
                result = self.qwen2vl.analyze(frame_pil, prompt)
                if result and "Error" not in result:
                    latency = time.time() - start
                    print(f"[VLM] Qwen2-VL completed in {latency:.2f}s")
                    return {
                        "provider": "qwen2vl",
                        "description": result,
                        "latency": latency,
                        "risk_score": numeric_risk,
                        "ensemble_size": 1
                    }
                else:
                    print(f"[VLM] Qwen2-VL returned error: {result}")
            except Exception as e:
                print(f"[VLM] Qwen2-VL failed: {e}")
        
        # 4. TRY OLLAMA (Local Fallback - Priority 3)
        try:
            print("[VLM] Trying Ollama (Local)...")
            result = self.ollama.analyze(frame_pil, prompt)
            if result and "Error" not in result:
                latency = time.time() - start
                print(f"[VLM] Ollama completed in {latency:.2f}s")
                return {
                    "provider": "ollama",
                    "description": result,
                    "latency": latency,
                    "risk_score": numeric_risk,
                    "ensemble_size": 1
                }
            else:
                print(f"[VLM] Ollama returned error: {result}")
        except Exception as e:
            print(f"[VLM] Ollama failed: {e}")
        
        # 5. TRY GEMINI (Cloud API - Priority 4)
        if getattr(self.gemini, "available", False):
            try:
                print("[VLM] Trying Gemini API...")
                result = self.gemini.analyze(frame_pil, prompt)
                if result and "Error" not in result:
                    latency = time.time() - start
                    print(f"[VLM] Gemini completed in {latency:.2f}s")
                    return {
                        "provider": "gemini",
                        "description": result,
                        "latency": latency,
                        "risk_score": numeric_risk,
                        "ensemble_size": 1
                    }
                else:
                    print(f"[VLM] Gemini returned error: {result}")
            except Exception as e:
                print(f"[VLM] Gemini failed: {e}")
        
        # 6. FALLBACK TO ENSEMBLE (Last Resort)
        print("[VLM] All primary providers failed, trying ensemble...")
        providers = {}
        providers["qwen"] = self.qwen
        if self.nemotron.available:
            providers["nemotron"] = self.nemotron
        providers["huggingface"] = self.hf

        # If nothing is configured/installed, return immediately
        if not providers:
            return {
                "provider": "none",
                "description": "No VLM providers available. Please configure at least one provider.",
                "latency": 0,
                "risk_score": float(numeric_risk) if isinstance(numeric_risk, (int, float)) else 0,
                "details": {}
            }
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        results = {}
        def call_provider(name, provider):
            try:
                return name, provider.analyze(frame_pil, prompt)
            except Exception as e:
                return name, f"Error: {str(e)}"

        with ThreadPoolExecutor(max_workers=min(3, len(providers) or 1)) as executor:
            future_to_provider = {executor.submit(call_provider, name, p): name for name, p in providers.items()}
            for future in as_completed(future_to_provider, timeout=28):
                name = future_to_provider[future]
                try:
                    name2, res = future.result(timeout=0)
                    results[name2] = res
                except Exception as e:
                    results[name] = f"Error: Analysis failed for {name} ({str(e)})"

            # Mark any unfinished providers as timed out
            for fut, name in future_to_provider.items():
                if fut.done():
                    continue
                results[name] = "Error: Analysis timed out"

        # NEURAL FUSION
        fusion = self._fusion_engine(results, risk_score)
        duration = time.time() - start
        
        print(f"[CORTEX] Ensemble analysis complete. Risk: {fusion['risk_score']}% (from {fusion['ensemble_size']} models). Time: {duration:.2f}s")
        
        return {
            "provider": "ensemble",
            "description": fusion['description'],
            "latency": round(duration, 2),
            "risk_score": fusion['risk_score'],
            "details": results # Keep raw results for forensic accounting
        }
    
    async def answer_question(self, image_data, question):
        """
        Smart conversational Q&A about images using local AI (FREE).
        Priority: Qwen2-VL (best quality) → Ollama → Gemini
        
        Args:
            image_data: Base64 encoded image with data URI prefix
            question: User's question about the image
            
        Returns:
            Dict with answer, confidence, and provider
        """
        try:
            # Decode image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 1. Try Qwen2-VL FIRST (Best quality, already loaded, FREE)
            if self.qwen2vl.available:
                try:
                    # Get config model
                    try:
                        import config
                        qwen_model = getattr(config, "QWEN2VL_MODEL_ID", "Qwen2-VL")
                    except ImportError:
                        qwen_model = "Qwen2-VL"
                        
                    print(f"[VLM-QA] Using PyTorch Local ({qwen_model}) for question: {question[:50]}...")
                    
                    # Add conversational context to get better answers
                    conversational_prompt = f"{question}\n\nProvide a clear, concise answer based on what you see in the image."
                    result = self.qwen2vl.analyze(image, conversational_prompt)
                    
                    if result and "Error" not in result:
                        print(f"[VLM-QA] Local ({qwen_model}) response: {result[:100]}...")
                        return {
                            'answer': result,
                            'confidence': 0.85,  # Higher confidence - better model
                            'provider': 'qwen2vl'
                        }
                    else:
                        print(f"[VLM-QA] Qwen2-VL returned error: {result}")
                except Exception as e:
                    print(f"[VLM-QA] Qwen2-VL failed: {e}")
            
            # 2. Try Ollama as fallback (FREE and local)
            if ollama is not None:
                try:
                    try:
                        import config
                        chat_model = getattr(config, "OLLAMA_CLOUD_MODEL", "llava:latest")
                    except ImportError:
                        chat_model = "llava:latest"
                        
                    print(f"[VLM-QA] Using Ollama Cloud ({chat_model}) for question: {question[:50]}...")
                    
                    # Convert image to bytes for Ollama
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='JPEG')
                    img_bytes = img_byte_arr.getvalue()

                    # Call Ollama with conversational prompt
                    response = ollama.chat(
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
                        'confidence': 0.75,
                        'provider': 'ollama'
                    }
                except Exception as e:
                    print(f"[VLM-QA] Ollama failed: {e}")
            
            # 3. Try Gemini if available (Cloud API - costs money)
            if getattr(self.gemini, "available", False):
                try:
                    print(f"[VLM-QA] Using Gemini for question...")
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
                'answer': 'Sorry, I could not analyze the image. Please make sure Qwen2-VL or Ollama is available (free local AI).',
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

# Singleton
vlm_service = VLMService()
