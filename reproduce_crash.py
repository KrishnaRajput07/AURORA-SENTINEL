import asyncio
import websockets
import cv2
import numpy as np
import json

async def test_crash():
    uri = "ws://localhost:8000/ws/live-feed"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Create a dummy blank image (black frame)
            # 640x480 RGB
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', img)
            
            print("Sending frames...")
            for i in range(20): # Send 20 frames to simulate a quick burst
                await websocket.send(buffer.tobytes())
                print(f"Sent frame {i}")
                
                try:
                    # Wait for response (expecting 2 messages: json and bytes)
                    msg1 = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    # print(f"Received: {len(msg1)} bytes type: {type(msg1)}")
                    if isinstance(msg1, str):
                        print(f"Response JSON: {msg1[:50]}...")
                    
                    msg2 = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    # print(f"Received frame back: {len(msg2)} bytes")
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by server!")
                    break
                    
                await asyncio.sleep(0.1)
                
            print("Finished sending frames.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_crash())
