import os
import time
from abc import ABC, abstractmethod
import google.generativeai as genai
import ollama

class VLMProvider(ABC):
    @abstractmethod
    def analyze(self, image, prompt):
        pass

class GeminiProvider(VLMProvider):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment.")
        else:
            genai.configure(api_key=api_key)
            # Use Flash as confirmed by user (high rate limits)
            self.model = genai.GenerativeModel('gemini-2.0-flash') 

    def analyze(self, image, prompt):
        if not hasattr(self, 'model'):
             # Lazy check: Try to load again (maybe env loaded late)
             api_key = os.getenv("GEMINI_API_KEY")
             if api_key:
                 genai.configure(api_key=api_key)
                 self.model = genai.GenerativeModel('gemini-2.0-flash')
             else:
                 return "Error: Gemini not configured (Check .env)"
        
        try:
            # Gemini accepts PIL images directly
            # Ensure image is PIL format before here
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return f"Error: {e}"

class OllamaProvider(VLMProvider):
    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llava")

    def analyze(self, image, prompt):
        try:
            # Convert PIL to Bytes for Ollama
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            # Ollama Python client handles image bytes or path
            response = ollama.chat(
                model=self.model_name,
                keep_alive=-1, # Keep model loaded, rely on OS paging for RAM
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                        'images': [img_bytes] 
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Ollama Error: {e}")
            return f"Error: {e}"

class VLMService:
    def __init__(self):
        # Default to Gemini, fallback to Ollama if env var says so
        self.provider_name = os.getenv("VLM_PROVIDER", "gemini").lower()
        print(f"Initializing VLM Service with provider: {self.provider_name}")
        
        if self.provider_name == "ollama":
            self.provider = OllamaProvider()
        else:
            self.provider = GeminiProvider()

    def analyze_scene(self, frame_pil, prompt="Describe this surveillance scene concisely. Highlight any threats."):
        """
        Analyze a frame using the configured provider.
        Args:
            frame_pil: PIL Image object
            prompt: Text prompt
        """
        start = time.time()
        print(f"[{self.provider_name}] Starting analysis...")
        result = self.provider.analyze(frame_pil, prompt)
        duration = time.time() - start
        print(f"[{self.provider_name}] Analysis complete. Time: {duration:.2f}s")
        
        return {
            "provider": self.provider_name,
            "description": result,
            "latency": round(duration, 2)
        }

# Singleton
vlm_service = VLMService()
