import cv2
import numpy as np
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
# logging config
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Handle video processing, summarization, and clip extraction
    """
    def __init__(self, output_dir='data/processed'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def summarize_video(self, video_path, alert_timestamps):
        """
        Create video summary with highlighted events
        
        Args:
            video_path: Path to input video
            alert_timestamps: List of timestamps (seconds) with alerts
        
        Returns:
            Path to summary video
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._create_summary,
            video_path,
            alert_timestamps
        )
    
    def _create_summary(self, video_path, alert_timestamps):
        """Synchronous video summarization"""
        if not alert_timestamps:
            return None

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Could not open video {video_path}")
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Output video
        output_path = self.output_dir / f"summary_{Path(video_path).stem}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        # Extract clips around alert timestamps
        clip_duration = 5  # seconds before and after
        
        # Merge overlapping intervals
        intervals = []
        for t in sorted(alert_timestamps):
            start = max(0, t - clip_duration)
            end = t + clip_duration
            if not intervals:
                intervals.append([start, end])
            else:
                last_start, last_end = intervals[-1]
                if start <= last_end:
                    intervals[-1][1] = max(last_end, end)
                else:
                    intervals.append([start, end])
        
        for start_sec, end_sec in intervals:
            start_frame = int(start_sec * fps)
            end_frame = int(end_sec * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            for _ in range(end_frame - start_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add timestamp overlay
                timestamp_text = f"Alert Segment"
                cv2.putText(
                    frame,
                    timestamp_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )
                
                out.write(frame)
        
        cap.release()
        out.release()

        # Transcode mp4v → H.264 + faststart for browser compatibility.
        # mp4v plays on desktop but shows blank in all browsers.
        try:
            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                winget_path = (
                    r"C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages"
                    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                    r"\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
                )
                if os.path.exists(winget_path):
                    ffmpeg = winget_path

            if ffmpeg:
                tmp_h264 = str(output_path).replace(".mp4", "._h264_tmp.mp4")
                cmd = [
                    ffmpeg, "-y",
                    "-i", str(output_path),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    "-preset", "ultrafast",
                    tmp_h264,
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode == 0 and os.path.exists(tmp_h264) and os.path.getsize(tmp_h264) > 1000:
                    os.replace(tmp_h264, str(output_path))
                    logger.info(f"Summary transcoded to H.264: {output_path}")
                else:
                    logger.warning(
                        f"ffmpeg transcode failed for summary clip (exit {proc.returncode}). "
                        f"File will NOT play in browsers. stderr: {proc.stderr[-300:]}"
                    )
                    if os.path.exists(tmp_h264):
                        os.remove(tmp_h264)
            else:
                logger.warning(
                    "ffmpeg not found — summary clip saved as mp4v and will NOT play in browsers."
                )
        except Exception as e:
            logger.warning(f"ffmpeg transcode error for summary: {e}")

        logger.info(f"Summary created: {output_path}")
        return str(output_path)
    
    async def extract_thumbnail(self, video_path, timestamp):
        """Extract thumbnail at specific timestamp"""
        cap = cv2.VideoCapture(str(video_path))
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if ret:
            thumbnail_path = self.output_dir / f"thumb_{Path(video_path).stem}_{timestamp}.jpg"
            cv2.imwrite(str(thumbnail_path), frame)
            cap.release()
            return str(thumbnail_path)
        
        cap.release()
        return None
