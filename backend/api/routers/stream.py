from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.ml_service import ml_service
import cv2
import numpy as np

router = APIRouter()

@router.websocket("/live-feed")
async def websocket_live_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video processing
    Optimized: Frame skipping + Resizing
    """
    await websocket.accept()
    print("WebSocket connected (Optimized)")
    
    frame_count = 0
    SKIP_FRAMES = 2 # Process 1 out of every 3 frames
    
    cached_result = {
        "detection": {"poses": [], "objects": []}, 
        "risk_score": 0, 
        "alert": None,
        "faces": [] # Cache for faces
    }

    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_bytes()
            
            if not ml_service.detector:
                await websocket.send_json({"error": "Models not loaded"})
                continue

            # Decode frame
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue
            
            # Optimization: Resize if too large
            height, width = frame.shape[:2]
            if width > 640:
                frame = cv2.resize(frame, (640, 480))

            # Process every Nth frame
            if frame_count % (SKIP_FRAMES + 1) == 0:
                # 1. Detect Objects/Poses
                detection = ml_service.detector.process_frame(frame)
                
                # 2. Detect Faces for Anonymizer (if needed)
                faces = []
                if ml_service.anonymizer:
                    faces = ml_service.anonymizer.detect_faces(frame)
                
                # 3. Calculate Risk
                risk_score, risk_factors = ml_service.risk_engine.calculate_risk(detection)
                
                # Check if risk_score is valid (not None) before checking > 50
                if risk_score is None:
                    risk_score = 0
                    
                if risk_score > 50:
                    alert = ml_service.risk_engine.generate_alert(risk_score, risk_factors)
                else:
                    alert = None

                # Update cache
                cached_result["detection"] = detection
                cached_result["risk_score"] = risk_score
                cached_result["alert"] = alert
                cached_result["faces"] = faces
            else:
                # Use cached results for skipped frames
                detection = cached_result["detection"]
                risk_score = cached_result["risk_score"]
                alert = cached_result["alert"]
                faces = cached_result["faces"]

            frame_count += 1
            
            # Anonymize frame using cached face rects
            if ml_service.anonymizer:
                anon_frame = ml_service.anonymizer.anonymize_frame(
                    frame,
                    poses=detection.get('poses', []),
                    mode='blur',
                    face_rects=faces
                )
            else:
                anon_frame = frame
            
            # ---------------------------
            # VISUALIZATION: Draw Tracking Overlays
            # ---------------------------
            # Draw persistent bounding boxes and IDs on the frame
            # This ensures the user sees the "perfect" tracking in action
            if detection and 'objects' in detection:
                for obj in detection['objects']:
                    x1, y1, x2, y2 = map(int, obj['bbox'])
                    track_id = obj.get('track_id', -1)
                    
                    # Choose color based on Track ID to differentiate people
                    color = (0, 255, 0) # Green default
                    if track_id != -1:
                        np.random.seed(int(track_id))
                        color = np.random.randint(0, 255, size=3).tolist()
                    
                    # Draw Box
                    cv2.rectangle(anon_frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw Label
                    label = f"{obj['class']} {track_id if track_id != -1 else ''}"
                    t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(anon_frame, (x1, y1 - t_size[1] - 5), (x1 + t_size[0], y1), color, -1)
                    cv2.putText(anon_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', anon_frame)
            
            # Send results
            await websocket.send_json({
                "risk_score": risk_score,
                "alert": alert,
                "detections": {
                    "person_count": len(detection.get('poses', [])),
                    "object_count": len(detection.get('objects', []))
                }
            })
            
            # Send processed frame
            await websocket.send_bytes(buffer.tobytes())
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
