import cv2
import numpy as np
import os

def test_codecs():
    codecs = ['mp4v', 'avc1', 'XVID', 'MJPG', 'H264']
    results = {}
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, "Test", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    for c in codecs:
        filename = f"test_{c}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*c)
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        
        if out.isOpened():
            out.write(frame)
            out.release()
            results[c] = f"Success (Size: {os.path.getsize(filename)} bytes)"
            # os.remove(filename)
        else:
            results[c] = "Failed to open"
            
    for c, res in results.items():
        print(f"Codec {c}: {res}")

if __name__ == "__main__":
    test_codecs()
