import os
import cv2
import time
import shutil
from datetime import datetime, timedelta
import threading

class Recording:
    def __init__(self, writer, path, start_time):
        self.writer = writer
        self.path = path
        self.start_time = start_time
        self.last_frame_time = start_time

class VideoStorageService:
    def __init__(self, base_path="storage"):
        self.base_path = base_path
        self.clips_path = os.path.join(base_path, "clips")
        self.bin_path = os.path.join(base_path, "bin")
        
        # Ensure directories exist
        os.makedirs(self.clips_path, exist_ok=True)
        os.makedirs(self.bin_path, exist_ok=True)
        
        self.active_recordings = {} # {camera_id: VideoWriter}
        self.cleanup_interval = 3600 # 1 hour
        self._start_cleanup_thread()

    def start_recording(self, camera_id, frame_size=(640, 480)):
        if camera_id in self.active_recordings:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{camera_id}_{timestamp}.mp4"
        filepath = os.path.join(self.clips_path, filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(filepath, fourcc, 10.0, frame_size)
        
        self.active_recordings[camera_id] = Recording(writer, filepath, time.time())
        print(f"Started smart recording for {camera_id}: {filename}")

    def add_frame(self, camera_id, frame):
        if camera_id not in self.active_recordings:
            return
        
        recording = self.active_recordings[camera_id]
        recording.writer.write(frame)
        recording.last_frame_time = time.time()
        
        # Auto-stop after 30 seconds of recording to chunk files
        if time.time() - recording.start_time > 30:
            self.stop_recording(camera_id)

    def stop_recording(self, camera_id):
        if camera_id not in self.active_recordings:
            return
        
        recording = self.active_recordings.pop(camera_id)
        recording.writer.release()
        print(f"Stopped recording for {camera_id}")

    def _start_cleanup_thread(self):
        thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        thread.start()

    def _cleanup_loop(self):
        while True:
            self.run_smart_cleanup()
            time.sleep(self.cleanup_interval)

    def run_smart_cleanup(self):
        """
        Industry standard cleanup: 
        - Move files older than 24h to Bin.
        - Delete files from Bin older than 7 days.
        """
        now = datetime.now()
        
        # 1. Clips -> Bin (Older than 24h)
        for f in os.listdir(self.clips_path):
            file_path = os.path.join(self.clips_path, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - mtime > timedelta(hours=24):
                print(f"Moving {f} to Smart Bin")
                shutil.move(file_path, os.path.join(self.bin_path, f))
        
        # 2. Bin -> Trash (Older than 7 days)
        for f in os.listdir(self.bin_path):
            file_path = os.path.join(self.bin_path, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - mtime > timedelta(days=7):
                print(f"Deleting expired clip from bin: {f}")
                os.remove(file_path)

video_storage_service = VideoStorageService()
