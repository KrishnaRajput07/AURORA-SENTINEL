import os
import cv2
import time
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
import threading


# 3 dirname calls: video_storage_service.py → services/ → backend/ → project root
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)


class VideoSegmentNotFoundError(Exception):
    """Raised when a video segment cannot be retrieved for the given camera and time range."""
    pass


class Recording:
    def __init__(self, writer, path, start_time):
        self.writer = writer
        self.path = path
        self.start_time = start_time
        self.last_frame_time = start_time

class VideoStorageService:
    def __init__(self, base_path=None):
        # Default to project root's storage directory
        if base_path is None:
            base_path = os.path.join(_PROJECT_ROOT, "storage")
        self.base_path = base_path
        self.clips_path = os.path.join(base_path, "clips")
        self.bin_path = os.path.join(base_path, "bin")
        self.live_retention_hours = int(os.getenv("LIVE_CLIP_RETENTION_HOURS", "24"))
        self.bin_retention_days = int(os.getenv("BIN_RETENTION_DAYS", "7"))
        
        # Ensure directories exist
        os.makedirs(self.clips_path, exist_ok=True)
        os.makedirs(self.bin_path, exist_ok=True)
        
        self.active_recordings = {} # {camera_id: VideoWriter}
        self.recordings_lock = threading.Lock()
        self.cleanup_interval = 3600 # 1 hour
        self._start_cleanup_thread()

    def start_recording(self, camera_id, frame_size=(640, 480)):
        with self.recordings_lock:
            if camera_id in self.active_recordings:
                return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{camera_id}_{timestamp}.mp4"
        filepath = os.path.join(self.clips_path, filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(filepath, fourcc, 10.0, frame_size)

        with self.recordings_lock:
            self.active_recordings[camera_id] = Recording(writer, filepath, time.time())
        print(f"Started smart recording for {camera_id}: {filename}")

    def add_frame(self, camera_id, frame):
        with self.recordings_lock:
            recording = self.active_recordings.get(camera_id)
        if recording is None:
            return

        recording.writer.write(frame)
        recording.last_frame_time = time.time()
        
        # Auto-stop after 30 seconds of recording to chunk files
        # But ensure minimum 5 seconds to get meaningful content
        if time.time() - recording.start_time > 30:
            self.stop_recording(camera_id)
            print(f"Auto-stopped recording for {camera_id} after 30s chunk")

    def stop_recording(self, camera_id):
        with self.recordings_lock:
            recording = self.active_recordings.pop(camera_id, None)
        if recording is None:
            return

        recording.writer.release()
        
        # Verify the file was written properly
        try:
            file_size = os.path.getsize(recording.path)
            if file_size < 1000:  # Less than 1KB means likely corrupted
                print(f"WARNING: Recording file too small ({file_size} bytes), removing: {recording.path}")
                os.remove(recording.path)
            else:
                print(f"Successfully stopped recording for {camera_id}: {recording.path} ({file_size} bytes)")
        except OSError as e:
            print(f"Error checking recording file {recording.path}: {e}")
        
        print(f"Stopped recording for {camera_id}")

    def is_recording(self, camera_id):
        with self.recordings_lock:
            return camera_id in self.active_recordings

    def stop_all_recordings(self):
        with self.recordings_lock:
            camera_ids = list(self.active_recordings.keys())
        for camera_id in camera_ids:
            self.stop_recording(camera_id)

    def _start_cleanup_thread(self):
        thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        thread.start()

    def _cleanup_loop(self):
        while True:
            try:
                self.run_smart_cleanup()
            except Exception as e:
                # Keep daemon alive on transient filesystem/runtime errors.
                print(f"Smart cleanup error: {e}")
            time.sleep(self.cleanup_interval)

    def run_smart_cleanup(self):
        """
        Industry standard cleanup:
        - Move files older than LIVE_CLIP_RETENTION_HOURS to Bin.
        - Delete files from Bin older than BIN_RETENTION_DAYS.
        """
        now = datetime.now()
        
        # 1. Clips -> Bin
        for f in os.listdir(self.clips_path):
            file_path = os.path.join(self.clips_path, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - mtime > timedelta(hours=self.live_retention_hours):
                print(f"Moving {f} to Smart Bin")
                shutil.move(file_path, os.path.join(self.bin_path, f))
        
        # 2. Bin -> Trash
        for f in os.listdir(self.bin_path):
            file_path = os.path.join(self.bin_path, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - mtime > timedelta(days=self.bin_retention_days):
                print(f"Deleting expired clip from bin: {f}")
                os.remove(file_path)

    def get_segment(self, camera_id: str, end_time: datetime, duration_seconds: int) -> bytes:
        """
        Retrieve `duration_seconds` of video ending at `end_time` for `camera_id`.
        Returns raw MP4 bytes encoded as H.264 for browser compatibility.
        Raises VideoSegmentNotFoundError on failure.
        """
        # Find completed (closed) recording files for this camera.
        # Skip any file that is currently open for writing (moov atom not finalized).
        active_paths = {
            rec.path for rec in self.active_recordings.values()
        }

        try:
            candidates = [
                f for f in os.listdir(self.clips_path)
                if f.startswith(camera_id) and f.endswith(".mp4")
                and os.path.join(self.clips_path, f) not in active_paths
            ]
        except OSError as e:
            raise VideoSegmentNotFoundError(
                f"Could not list recordings for camera '{camera_id}': {e}"
            ) from e

        if not candidates:
            raise VideoSegmentNotFoundError(
                f"No completed recording files found for camera '{camera_id}'. "
                f"The current recording chunk may still be open."
            )

        # Pick the most recently modified completed file
        candidates.sort(
            key=lambda f: os.path.getmtime(os.path.join(self.clips_path, f)),
            reverse=True,
        )
        source_path = os.path.join(self.clips_path, candidates[0])

        # Get actual file duration via ffprobe
        try:
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    source_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            file_duration = float(probe.stdout.decode().strip())
        except Exception:
            file_duration = 30.0  # fallback

        start_offset = max(0.0, file_duration - duration_seconds)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start_offset),
                "-i", source_path,
                "-t", str(duration_seconds),
                "-vcodec", "libx264",          # H.264 for browser compatibility
                "-acodec", "aac",
                "-preset", "ultrafast",
                "-movflags", "frag_keyframe+empty_moov+faststart",
                tmp_path,
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            if result.returncode != 0:
                raise VideoSegmentNotFoundError(
                    f"FFmpeg failed for camera '{camera_id}' "
                    f"(exit {result.returncode}): {result.stderr.decode(errors='replace')}"
                )

            with open(tmp_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired as e:
            raise VideoSegmentNotFoundError(
                f"FFmpeg timed out for camera '{camera_id}'"
            ) from e
        except FileNotFoundError as e:
            raise VideoSegmentNotFoundError(
                f"FFmpeg executable not found: {e}"
            ) from e
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


video_storage_service = VideoStorageService()
