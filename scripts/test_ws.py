import asyncio
import websockets
import sys

async def test_connection():
    uri = "ws://localhost:8000/ws/live-feed"
    print(f"Attempting to connect to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Successfully connected to WebSocket!")
            await websocket.close()
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    try:
        if asyncio.run(test_connection()):
            print("Test passed.")
            sys.exit(0)
        else:
            print("Test failed.")
            sys.exit(1)
    except ImportError:
        print("websockets library not installed. Please install with 'pip install websockets'")
