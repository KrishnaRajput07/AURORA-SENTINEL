"""
Enhanced AI Intelligence Router
Supports: Qwen2-VL (GPU), Ollama (Local), HuggingFace (Fallback)
"""
import os
import sys
import base64
import json
from io import BytesIO
from PIL import Image
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import model availability tracker
from model_availability import get_tracker

# Global model cache
_models = {}
_qwen2vl_analyzer = None
_ollama_available = False
_nemotron_provider = None
_availability_tracker = get_tracker()

# Load config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
    PRIMARY_PROVIDER = getattr(config, "PRIMARY_VLM_PROVIDER", "qwen2vl_local")
    OLLAMA_MODEL = getattr(config, "OLLAMA_CLOUD_MODEL", "qwen3-vl:235b-cloud")
    QWEN2VL_MODEL = getattr(config, "QWEN2VL_MODEL_ID", "Qwen2-VL")
except ImportError:
    PRIMARY_PROVIDER = "qwen2vl_local"
    OLLAMA_MODEL = "qwen3-vl:235b-cloud"
    QWEN2VL_MODEL = "Qwen2-VL"


def init_qwen2vl():
    """
    Initialize Qwen2-VL model.
    Handles load failure gracefully (Requirement 6.1).
    
    Returns:
        Qwen2VLAnalyzer instance or None if load fails
    """
    global _qwen2vl_analyzer
    
    if _qwen2vl_analyzer is not None:
        return _qwen2vl_analyzer
    
    try:
        from qwen2vl_integration import Qwen2VLAnalyzer
        logger.info("Loading Qwen2-VL-2B-Instruct...")
        _qwen2vl_analyzer = Qwen2VLAnalyzer()
        logger.info("✅ Qwen2-VL loaded successfully")
        _availability_tracker.record_success('qwen2vl')
        return _qwen2vl_analyzer
    except Exception as e:
        logger.error(f"❌ Qwen2-VL load failed: {e}")
        _availability_tracker.record_failure('qwen2vl', e)
        return None

def init_ollama():
    """
    Check if Ollama is available.
    Handles initialization failure gracefully (Requirement 6.1).
    
    Returns:
        True if Ollama is available, False otherwise
    """
    global _ollama_available
    
    try:
        import ollama
        ollama.list()  # Test if Ollama service is running
        _ollama_available = True
        logger.info("✅ Ollama available")
        _availability_tracker.record_success('ollama')
        return True
    except Exception as e:
        logger.error(f"❌ Ollama not available: {e}")
        _ollama_available = False
        _availability_tracker.record_failure('ollama', e)
        return False

def init_nemotron():
    """
    Initialize Nemotron verification model.
    Handles load failure gracefully - logs and continues (Requirement 6.2).
    
    Returns:
        NemotronProvider instance or None if load fails
    """
    global _nemotron_provider
    
    if _nemotron_provider is not None:
        return _nemotron_provider
    
    try:
        # Import from backend services
        import sys
        import os
        backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'services')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        from vlm_service import NemotronProvider
        logger.info("Loading Nemotron verification model...")
        _nemotron_provider = NemotronProvider()
        if _nemotron_provider.available:
            logger.info("✅ Nemotron loaded successfully")
            _availability_tracker.record_success('nemotron')
            return _nemotron_provider
        else:
            logger.warning("❌ Nemotron not available (model load failed)")
            _availability_tracker.record_failure('nemotron')
            _nemotron_provider = None
            return None
    except Exception as e:
        logger.error(f"❌ Nemotron load failed: {e}")
        _availability_tracker.record_failure('nemotron', e)
        _nemotron_provider = None
        return None

def decode_base64_image(image_data):
    """Decode base64 image to PIL Image"""
    try:
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        return image
    except Exception as e:
        logger.error(f"Failed to decode image: {e}")
        return None

def analyze_with_qwen2vl(image, ml_score, ml_factors):
    """Analyze using Qwen2-VL (GPU-accelerated)"""
    # Check availability before attempting
    if not _availability_tracker.is_available('qwen2vl'):
        logger.info("[Qwen2-VL] Model unavailable (in cooldown), skipping")
        return None
    
    try:
        analyzer = init_qwen2vl()
        if not analyzer:
            _availability_tracker.record_failure('qwen2vl')
            return None
        
        logger.info("[Qwen2-VL] Analyzing image...")
        
        # Create prompt based on ML score
        if ml_score > 70:
            prompt = """Analyze this image for violence or fighting in a PUBLIC SURVEILLANCE context.

Classify as ONE of these categories:
1. REAL_FIGHT: Physical aggression, assault, or attack (NO protective gear)
2. ORGANIZED_SPORT: Boxing/martial arts WITH protective gear (gloves, headgear) AND referee/ring
3. SUSPICIOUS: Crowd surrounding two people (concealment behavior) OR unknown items in suspicious contexts
4. NORMAL: Safe activity, no threats

DO NOT classify as "prank" or "drama" - any physical aggression without sport indicators is REAL_FIGHT.

Sport indicators: protective gear (boxing gloves, headgear), referee present, ring/mat structure
Heavy fighting indicators: multiple strikes, sustained aggression, visible injury

Risk scoring:
- REAL_FIGHT with heavy fighting (multiple strikes, sustained aggression, visible injury): 80-95
- REAL_FIGHT without heavy indicators: 75-90
- ORGANIZED_SPORT: 20-35 (capped)
- SUSPICIOUS: 60-75
- NORMAL: 10-25

Respond in JSON format:
{"aiScore": <0-100>, "sceneType": "<real_fight|organized_sport|suspicious|normal>", "explanation": "<what you see>", "confidence": <0.0-1.0>}"""
        else:
            prompt = """Describe what you see in this image in a PUBLIC SURVEILLANCE context.

Look for:
- Any signs of violence, fighting, or aggressive behavior
- Sport indicators: protective gear, referee, ring structure
- Suspicious behavior: crowd surrounding people, unknown items
- Normal safe activity

DO NOT classify as "prank" or "drama" - any physical aggression is a real threat unless sport indicators are present."""
        
        # Prepare messages for Qwen2-VL
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        image.save(temp_file.name)
        temp_file.close()
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": temp_file.name},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            
            # Process with Qwen2-VL
            text = analyzer.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = analyzer.process_vision_info(messages)
            
            inputs = analyzer.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to(analyzer.device)
            
            # Generate
            with torch.no_grad():
                generated_ids = analyzer.model.generate(**inputs, max_new_tokens=256)
            
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            response = analyzer.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            
            logger.info(f"[Qwen2-VL] Response: {response[:200]}")
            
            # Parse response
            result = parse_ai_response(response, ml_score)
            result['provider'] = 'qwen2vl'
            
            # Record success
            _availability_tracker.record_success('qwen2vl')
            
            return result
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
        
    except Exception as e:
        logger.error(f"Qwen2-VL analysis failed: {e}")
        _availability_tracker.record_failure('qwen2vl', e)
        return None

def analyze_with_ollama(image, ml_score, ml_factors):
    """Analyze using Ollama"""
    # Check availability before attempting
    if not _availability_tracker.is_available('ollama'):
        logger.info("[Ollama] Model unavailable (in cooldown), skipping")
        return None
    
    try:
        if not _ollama_available and not init_ollama():
            _availability_tracker.record_failure('ollama')
            return None
        
        import ollama
        import io
        
        logger.info("[Ollama] Analyzing image...")
        
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Create prompt
        if ml_score > 70:
            prompt = """Analyze this image for violence or fighting in a PUBLIC SURVEILLANCE context.

Classify as ONE of these categories:
1. REAL_FIGHT: Physical aggression, assault, or attack (NO protective gear)
2. ORGANIZED_SPORT: Boxing/martial arts WITH protective gear (gloves, headgear) AND referee/ring
3. SUSPICIOUS: Crowd surrounding two people (concealment behavior) OR unknown items in suspicious contexts
4. NORMAL: Safe activity, no threats

DO NOT classify as "prank" or "drama" - any physical aggression without sport indicators is REAL_FIGHT.

Sport indicators: protective gear (boxing gloves, headgear), referee present, ring/mat structure
Heavy fighting indicators: multiple strikes, sustained aggression, visible injury

Risk scoring:
- REAL_FIGHT with heavy fighting: 80-95
- REAL_FIGHT without heavy indicators: 75-90
- ORGANIZED_SPORT: 20-35 (capped)
- SUSPICIOUS: 60-75
- NORMAL: 10-25

Provide a risk score (0-100) and explain what you see."""
        else:
            prompt = """Describe what you see in this image in a PUBLIC SURVEILLANCE context.

Look for:
- Any signs of violence, fighting, or aggressive behavior
- Sport indicators: protective gear, referee, ring structure
- Suspicious behavior: crowd surrounding people, unknown items
- Normal safe activity

DO NOT classify as "prank" or "drama" - any physical aggression is a real threat unless sport indicators are present."""
        
        # Call Ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [img_bytes]
            }]
        )
        
        response_text = response['message']['content']
        logger.info(f"[Ollama] Response: {response_text[:200]}")
        
        # Parse response
        result = parse_ai_response(response_text, ml_score)
        result['provider'] = 'ollama'
        
        # Record success
        _availability_tracker.record_success('ollama')
        
        return result
        
    except Exception as e:
        logger.error(f"Ollama analysis failed: {e}")
        _availability_tracker.record_failure('ollama', e)
        return None

def parse_ai_response(response_text, ml_score):
    """
    Parse AI response with keyword-based fallback (NO hardcoded scores).

    Args:
        response_text: Raw text from AI model
        ml_score: ML risk score for context (not used for fallback scoring)

    Returns:
        {
            'aiScore': int (0-100),
            'sceneType': str ('real_fight' | 'organized_sport' | 'normal' | 'suspicious'),
            'explanation': str,
            'confidence': float (0-1)
        }
    """
    import re

    # Try to extract JSON first
    try:
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            ai_score = int(parsed.get('aiScore', 0))
            scene_type = parsed.get('sceneType', 'normal')

            # Validate and normalize scene type (remove deprecated types)
            if scene_type in ['drama', 'prank', 'staged', 'performance']:
                scene_type = 'normal'
            elif scene_type == 'boxing':
                scene_type = 'organized_sport'

            return {
                'aiScore': ai_score,
                'sceneType': scene_type,
                'explanation': parsed.get('explanation', response_text),
                'confidence': float(parsed.get('confidence', 0.75))
            }
    except:
        pass

    # Fallback: keyword-based analysis (NO hardcoded scores)
    lower_text = response_text.lower()

    # Define keyword patterns
    fight_keywords = ['fight', 'fighting', 'violence', 'assault', 'attack', 'punch', 'kick',
                      'hitting', 'striking', 'aggressive', 'aggression', 'brawl']
    heavy_fight_keywords = ['multiple strikes', 'sustained aggression', 'visible injury', 'blood',
                            'weapon', 'knife', 'gun', 'severe', 'brutal']
    sport_keywords = ['boxing', 'martial arts', 'training', 'sparring', 'controlled',
                      'protective gear', 'gloves', 'headgear', 'referee', 'ring', 'mat']
    suspicious_keywords = ['crowd surrounding', 'people covering', 'concealment', 'unknown item',
                           'suspicious object', 'suspicious behavior']
    normal_keywords = ['normal', 'safe', 'walking', 'standing', 'talking', 'conversation',
                       'no threat', 'peaceful']

    # Check for sport indicators first
    has_sport_indicators = any(keyword in lower_text for keyword in sport_keywords)

    # Check for heavy fighting
    has_heavy_fight = any(keyword in lower_text for keyword in heavy_fight_keywords)

    # Check for fight keywords
    has_fight = any(keyword in lower_text for keyword in fight_keywords)

    # Check for suspicious behavior
    has_suspicious = any(keyword in lower_text for keyword in suspicious_keywords)

    # Check for normal indicators
    has_normal = any(keyword in lower_text for keyword in normal_keywords)

    # Count keyword matches for score variation
    fight_count = sum(1 for kw in fight_keywords if kw in lower_text)
    heavy_fight_count = sum(1 for kw in heavy_fight_keywords if kw in lower_text)
    sport_count = sum(1 for kw in sport_keywords if kw in lower_text)
    suspicious_count = sum(1 for kw in suspicious_keywords if kw in lower_text)
    normal_count = sum(1 for kw in normal_keywords if kw in lower_text)

    # Determine scene type and score based on keyword analysis
    # Use keyword count to vary score within range (more keywords = higher score)
    if has_sport_indicators:
        # Sport indicators present: 20-35 range
        scene_type = 'organized_sport'
        # Vary score based on sport keyword count (1-5+ keywords)
        ai_score = min(20 + (sport_count * 3), 35)
        confidence = 0.7
    elif has_heavy_fight:
        # Heavy fighting indicators: 80-95 range
        scene_type = 'real_fight'
        # Vary score based on heavy fight keyword count
        ai_score = min(80 + (heavy_fight_count * 5), 95)
        confidence = 0.85
    elif has_fight:
        # Fight keywords without sport indicators: 75-90 range
        scene_type = 'real_fight'
        # Vary score based on fight keyword count
        ai_score = min(75 + (fight_count * 3), 90)
        confidence = 0.8
    elif has_suspicious:
        # Suspicious indicators: 60-75 range
        scene_type = 'suspicious'
        # Vary score based on suspicious keyword count
        ai_score = min(60 + (suspicious_count * 5), 75)
        confidence = 0.65
    elif has_normal:
        # Normal indicators: 10-25 range
        scene_type = 'normal'
        # Vary score based on normal keyword count (inverse - more normal = lower score)
        ai_score = max(25 - (normal_count * 3), 10)
        confidence = 0.75
    else:
        # No clear indicators - default to normal with low confidence
        scene_type = 'normal'
        ai_score = 20
        confidence = 0.5

    return {
        'aiScore': ai_score,
        'sceneType': scene_type,
        'explanation': response_text[:300],
        'confidence': confidence
    }


def fallback_analysis(ml_score, ml_factors, error_details=None):
    """
    Rule-based fallback when no AI models available.
    Uses ML score as final score (Requirement 6.4).
    
    Args:
        ml_score: ML risk score (0-100)
        ml_factors: ML detection factors
        error_details: Optional dict with error information from failed models
        
    Returns:
        Dict with aiScore, sceneType, explanation, confidence, provider, errors
    """
    logger.warning("Using ML score as final (all AI models failed)")
    
    # Use ML score directly as AI score (Requirement 6.4)
    ai_score = int(ml_score) if ml_score is not None else 0
    scene_type = 'normal'
    explanation = 'ML-based analysis (AI models unavailable)'
    
    if ml_factors:
        factors_str = json.dumps(ml_factors).lower()
        
        if 'weapon' in factors_str:
            scene_type = 'real_fight'
            ai_score = max(ai_score, 80)
            explanation = 'Weapon detected - high threat (ML-based)'
        elif 'grappling' in factors_str or 'proximity' in factors_str:
            scene_type = 'real_fight'
            explanation = 'Close combat detected (ML-based)'
        elif 'aggression' in factors_str:
            scene_type = 'real_fight'
            explanation = 'Aggressive behavior detected (ML-based)'
    
    result = {
        'aiScore': ai_score,
        'sceneType': scene_type,
        'explanation': explanation,
        'confidence': 0.3,  # Low confidence when using ML only
        'provider': 'ml_fallback'
    }
    
    # Include error details if provided (Requirement 6.5)
    if error_details:
        result['errors'] = error_details
        logger.info(f"Error details included in response: {error_details}")
    
    return result

def analyze_image(image_data, ml_score, ml_factors, camera_id):
    """
    Main analysis function with comprehensive error handling.
    
    Implements error handling requirements:
    - Qwen2-VL failure → Ollama fallback (Req 6.1)
    - Nemotron failure → single-model analysis (Req 6.2)
    - Nemotron timeout → use Qwen score (Req 6.3)
    - Both AI models fail → use ML score (Req 6.4)
    - All error paths return valid score (Req 6.8)
    - Error details included in response (Req 6.5)
    - Latency tracking and timeout enforcement (Req 7.1-7.5)
    
    Args:
        image_data: Base64 encoded image
        ml_score: ML risk score (0-100)
        ml_factors: ML detection factors
        camera_id: Camera identifier
        
    Returns:
        Dict with aiScore, sceneType, explanation, confidence, provider, errors (if any), latency metrics
    """
    import time
    
    # Start total timer (Requirement 7.3: 5 second total timeout)
    total_start_time = time.time()
    TOTAL_TIMEOUT = 5.0  # seconds
    
    # Track errors for reporting (Requirement 6.5)
    error_details = {}
    
    # Track latency metrics (Requirement 7.5)
    latency_metrics = {
        'qwen2vl_ms': 0,
        'nemotron_ms': 0,
        'total_ms': 0
    }
    
    # Ensure ml_score is valid (never null/undefined)
    if ml_score is None:
        ml_score = 0
        logger.warning("ML score was None, defaulting to 0")
    
    # Skip analysis for very low scores (Requirement 7.6)
    if ml_score < 20:
        latency_metrics['total_ms'] = int((time.time() - total_start_time) * 1000)
        return {
            'aiScore': ml_score,
            'sceneType': 'normal',
            'explanation': 'Low-risk scene, no deep analysis needed',
            'confidence': 0.9,
            'provider': 'none',
            'latency_metrics': latency_metrics
        }
    
    # Decode image
    image = decode_base64_image(image_data)
    if not image:
        logger.error("Failed to decode image, using ML score as fallback")
        error_details['image_decode'] = 'Failed to decode base64 image'
        latency_metrics['total_ms'] = int((time.time() - total_start_time) * 1000)
        result = fallback_analysis(ml_score, ml_factors, error_details)
        result['latency_metrics'] = latency_metrics
        return result
    
    # Try models based on config priority
    if PRIMARY_PROVIDER == "ollama_cloud":
        logger.info("Configured for Ollama Cloud primary, trying Ollama...")
        # Check timeout
        elapsed_time = time.time() - total_start_time
        remaining_time = TOTAL_TIMEOUT - elapsed_time
        result = None
        
        if remaining_time >= 0.5:
            result = analyze_with_ollama(image, ml_score, ml_factors)
            
        if result:
            ai_score_raw = result['aiScore']
            final_score = int(0.3 * ml_score + 0.7 * result['aiScore'])
            result['aiScore'] = final_score
            result['weighted'] = True
            result['ml_score'] = ml_score
            result['ai_score_raw'] = ai_score_raw
            latency_metrics['total_ms'] = int((time.time() - total_start_time) * 1000)
            result['latency_metrics'] = latency_metrics
            if error_details:
                result['errors'] = error_details
            if result['aiScore'] is None:
                result['aiScore'] = ml_score
            return result
        else:
            error_details['ollama'] = 'Primary Ollama failed, falling back to Local model'
            logger.info(f"Primary ({OLLAMA_MODEL}) failed or timed out, falling back to Local ({QWEN2VL_MODEL})...")

    # Secondary or Primary is Qwen2-VL
    logger.info(f"Trying Local Provider ({QWEN2VL_MODEL})...")
    qwen_start_time = time.time()
    qwen_timeout = min(2.0, TOTAL_TIMEOUT - (time.time() - total_start_time))
    
    result = analyze_with_qwen2vl(image, ml_score, ml_factors)
    qwen_latency = time.time() - qwen_start_time
    latency_metrics['qwen2vl_ms'] = int(qwen_latency * 1000)
    
    # Log Qwen2-VL latency
    logger.info(f"[Latency] Qwen2-VL: {latency_metrics['qwen2vl_ms']}ms (target: 2000ms)")
    if qwen_latency > 2.0:
        logger.warning(f"[Latency] Qwen2-VL exceeded target: {latency_metrics['qwen2vl_ms']}ms > 2000ms")
    
    if result:
        # Qwen2-VL succeeded - try Nemotron verification
        qwen_summary = result.get('explanation', '')
        qwen_scene_type = result.get('sceneType', 'normal')
        qwen_ai_score = result.get('aiScore', 0)
        
        # Try Nemotron verification (Requirement 6.2, 6.3, 7.2)
        nemotron_verification = None
        nemotron_latency_ms = 0
        
        # Check if we have time left for Nemotron (Requirement 7.3)
        elapsed_time = time.time() - total_start_time
        remaining_time = TOTAL_TIMEOUT - elapsed_time
        
        if remaining_time < 0.5:
            # Not enough time for Nemotron - skip it (Requirement 7.4)
            logger.warning(f"[Timeout] Insufficient time for Nemotron ({remaining_time:.2f}s remaining), using Qwen score")
            error_details['nemotron'] = f'Skipped due to timeout (only {remaining_time:.2f}s remaining)'
        elif _availability_tracker.is_available('nemotron'):
            try:
                nemotron = init_nemotron()
                if nemotron and nemotron.available:
                    logger.info("[Nemotron] Verifying Qwen2-VL analysis...")
                    nemotron_start = time.time()
                    
                    # Requirement 7.2: Target 3 seconds for Nemotron
                    nemotron_timeout = min(3.0, remaining_time)
                    
                    nemotron_verification = nemotron.verify_analysis(
                        image=image,
                        qwen_summary=qwen_summary,
                        qwen_scene_type=qwen_scene_type,
                        qwen_risk_score=qwen_ai_score,
                        timeout=nemotron_timeout
                    )
                    
                    nemotron_latency_ms = int((time.time() - nemotron_start) * 1000)
                    latency_metrics['nemotron_ms'] = nemotron_latency_ms
                    
                    # Log Nemotron latency (Requirement 7.5)
                    logger.info(f"[Latency] Nemotron: {nemotron_latency_ms}ms (target: 3000ms)")
                    if nemotron_latency_ms > 3000:
                        logger.warning(f"[Latency] Nemotron exceeded target: {nemotron_latency_ms}ms > 3000ms")
                    
                    # Use Nemotron's recommended score if verification succeeded
                    if not nemotron_verification.get('timed_out', False):
                        result['aiScore'] = nemotron_verification['recommended_score']
                        result['confidence'] = nemotron_verification['confidence']
                        logger.info(f"[Nemotron] Adjusted AI score: {result['aiScore']} (confidence: {result['confidence']})")
                        
                        # Record success
                        _availability_tracker.record_success('nemotron')
                    else:
                        # Timeout - use Qwen score (Requirement 6.3)
                        logger.warning("[Nemotron] Verification timed out, using Qwen score")
                        error_details['nemotron'] = 'Verification timed out (>3s)'
                        _availability_tracker.record_failure('nemotron', Exception("Timeout"))
                else:
                    # Nemotron not available - continue with single-model (Requirement 6.2)
                    logger.info("[Nemotron] Not available, using Qwen score only")
                    error_details['nemotron'] = 'Model not available at initialization'
                    _availability_tracker.record_failure('nemotron')
            except Exception as e:
                # Nemotron failed - use Qwen score (Requirement 6.2)
                logger.warning(f"[Nemotron] Verification failed: {e}, using Qwen score")
                error_details['nemotron'] = f'Verification failed: {str(e)}'
                _availability_tracker.record_failure('nemotron', e)
        else:
            logger.info("[Nemotron] Model unavailable (in cooldown), skipping verification")
            error_details['nemotron'] = 'Model unavailable (in cooldown period)'
        
        # Always use weighted scoring: 30% ML + 70% AI
        ai_score_raw = result['aiScore']
        final_score = int(0.3 * ml_score + 0.7 * result['aiScore'])
        result['aiScore'] = final_score
        result['weighted'] = True
        result['ml_score'] = ml_score
        result['ai_score_raw'] = ai_score_raw
        
        # Include Nemotron verification details if available
        if nemotron_verification:
            result['nemotron_verification'] = nemotron_verification
            result['nemotron_latency_ms'] = nemotron_latency_ms
        
        # Calculate total latency (Requirement 7.5)
        latency_metrics['total_ms'] = int((time.time() - total_start_time) * 1000)
        result['latency_metrics'] = latency_metrics
        
        # Log total latency (Requirement 7.3, 7.5)
        logger.info(f"[Latency] Total analysis: {latency_metrics['total_ms']}ms (target: 5000ms)")
        if latency_metrics['total_ms'] > 5000:
            logger.warning(f"[Latency] Total analysis exceeded target: {latency_metrics['total_ms']}ms > 5000ms")
        
        # Include error details if any (Requirement 6.5)
        if error_details:
            result['errors'] = error_details
        
        # Ensure score is never null/undefined (Requirement 6.8)
        if result['aiScore'] is None:
            result['aiScore'] = ml_score
            logger.warning("AI score was None, using ML score as fallback")
        
        return result
    else:
        # Qwen2-VL failed
        error_details['qwen2vl'] = 'Analysis failed or model unavailable'

    if PRIMARY_PROVIDER == "ollama_cloud":
        pass
    else:    
        # 2. Ollama (Local fallback) - Requirement 6.1
        # Check if we have time left (Requirement 7.4)
        elapsed_time = time.time() - total_start_time
        remaining_time = TOTAL_TIMEOUT - elapsed_time
        
        if remaining_time < 0.5:
            # Not enough time for Ollama - use ML score (Requirement 7.4)
            logger.warning(f"[Timeout] Insufficient time for Ollama ({remaining_time:.2f}s remaining), using ML score")
            error_details['ollama'] = f'Skipped due to timeout (only {remaining_time:.2f}s remaining)'
            latency_metrics['total_ms'] = int((time.time() - total_start_time) * 1000)
            result = fallback_analysis(ml_score, ml_factors, error_details)
            result['latency_metrics'] = latency_metrics
            return result
        
        logger.info(f"Local ({QWEN2VL_MODEL}) failed, trying Cloud ({OLLAMA_MODEL}) fallback...")
        result = analyze_with_ollama(image, ml_score, ml_factors)
        
        if result:
            # Ollama succeeded
            # Always use weighted scoring: 30% ML + 70% AI
            ai_score_raw = result['aiScore']
            final_score = int(0.3 * ml_score + 0.7 * result['aiScore'])
            result['aiScore'] = final_score
            result['weighted'] = True
            result['ml_score'] = ml_score
            result['ai_score_raw'] = ai_score_raw
            
            # Calculate total latency (Requirement 7.5)
            latency_metrics['total_ms'] = int((time.time() - total_start_time) * 1000)
            result['latency_metrics'] = latency_metrics
            
            # Log total latency
            logger.info(f"[Latency] Total analysis (with Ollama fallback): {latency_metrics['total_ms']}ms")
            
            # Include error details (Requirement 6.5)
            if error_details:
                result['errors'] = error_details
            
            # Ensure score is never null/undefined (Requirement 6.8)
            if result['aiScore'] is None:
                result['aiScore'] = ml_score
                logger.warning("AI score was None, using ML score as fallback")
            
            return result
        else:
            # Ollama also failed - record error
            error_details['ollama'] = 'Analysis failed or model unavailable'
    
    # 3. Both AI models failed - use ML score as final (Requirement 6.4)
    logger.warning("Both Qwen2-VL and Ollama failed, using ML score as final")
    latency_metrics['total_ms'] = int((time.time() - total_start_time) * 1000)
    result = fallback_analysis(ml_score, ml_factors, error_details)
    result['latency_metrics'] = latency_metrics
    
    # Ensure score is never null/undefined (Requirement 6.8)
    if result['aiScore'] is None:
        result['aiScore'] = 0
        logger.error("Fallback analysis returned None, defaulting to 0")
    
    return result

def answer_question(image_data, question):
    """Answer a specific question about an image"""
    logger.info(f"Answering question: {question}")
    
    # Decode image
    image = decode_base64_image(image_data)
    if not image:
        return {
            'answer': 'Error: Could not decode image',
            'confidence': 0.0,
            'provider': 'error'
        }
    
    # Try Qwen2-VL first (best for questions)
    try:
        analyzer = init_qwen2vl()
        if analyzer:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            image.save(temp_file.name)
            temp_file.close()
            
            try:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": temp_file.name},
                            {"type": "text", "text": question},
                        ],
                    }
                ]
                
                text = analyzer.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                image_inputs, video_inputs = analyzer.process_vision_info(messages)
                
                inputs = analyzer.processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt",
                )
                inputs = inputs.to(analyzer.device)
                
                with torch.no_grad():
                    generated_ids = analyzer.model.generate(**inputs, max_new_tokens=256)
                
                generated_ids_trimmed = [
                    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                ]
                
                response = analyzer.processor.batch_decode(
                    generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )[0]
                
                return {
                    'answer': response,
                    'confidence': 0.8,
                    'provider': 'qwen2vl'
                }
            finally:
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)
    except Exception as e:
        logger.error(f"Qwen2-VL question failed: {e}")
    
    # Try Ollama
    try:
        if _ollama_available or init_ollama():
            import ollama
            import io
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            
            response = ollama.chat(
                model='llava:latest',  # Using llava:latest (7B model)
                messages=[{
                    'role': 'user',
                    'content': question,
                    'images': [img_bytes]
                }]
            )
            
            return {
                'answer': response['message']['content'],
                'confidence': 0.75,
                'provider': 'ollama'
            }
    except Exception as e:
        logger.error(f"Ollama question failed: {e}")
    
    return {
        'answer': 'Sorry, I could not analyze the image to answer your question.',
        'confidence': 0.0,
        'provider': 'error'
    }


def get_model_status():
    """
    Get availability status for all AI models.
    Used by health check endpoints.
    
    Returns:
        Dictionary with status for each model
    """
    return _availability_tracker.get_all_status()

if __name__ == "__main__":
    # Test the analyzer
    print("Testing Enhanced AI Analyzer...")
    
    # Create a dummy image
    dummy_image = Image.new('RGB', (640, 480), color='red')
    buffer = BytesIO()
    dummy_image.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode()
    
    result = analyze_image(
        image_data=f"data:image/jpeg;base64,{image_data}",
        ml_score=75,
        ml_factors={'aggression': 0.8, 'proximity': 0.6},
        camera_id='TEST-CAM'
    )
    
    print("Result:", json.dumps(result, indent=2))
