import cv2
import time
import os
from datetime import datetime
from threading import Thread, Event
import logging

logger = logging.getLogger(__name__)

class VideoCapture:
    def __init__(self, output_dir="records"):
        """Initialize the video capture system.
        
        Args:
            output_dir (str): Directory where recordings will be stored
        """
        self.output_dir = output_dir
        self.recording = False
        self._stop_event = Event()
        self._recording_thread = None
        self.current_video = None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def start_recording(self, filename=None):
        """Start recording the screen.
        
        Args:
            filename (str, optional): Custom filename for the recording.
                                    If None, generates timestamp-based filename.
        """
        if self.recording:
            logger.warning("Recording is already in progress")
            return
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.mp4"
            
        self.current_video = os.path.join(self.output_dir, filename)
        self._stop_event.clear()
        self.recording = True
        
        self._recording_thread = Thread(target=self._record)
        self._recording_thread.start()
        logger.info(f"Started recording to {self.current_video}")
        
    def stop_recording(self):
        """Stop the current recording if one is in progress."""
        if not self.recording:
            logger.warning("No recording in progress")
            return
            
        self._stop_event.set()
        if self._recording_thread:
            self._recording_thread.join()
        self.recording = False
        logger.info("Recording stopped")
        
    def _record(self):
        """Internal method that handles the actual recording process."""
        try:
            # Initialize screen capture
            import numpy as np
            from PIL import ImageGrab
            
            # Get screen size
            screen = ImageGrab.grab()
            width, height = screen.size
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.current_video, fourcc, 20.0, (width, height))
            
            while not self._stop_event.is_set():
                # Capture screen
                frame = np.array(ImageGrab.grab())
                # Convert from RGB to BGR (OpenCV uses BGR)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Write frame
                out.write(frame)
                
                # Small sleep to reduce CPU usage
                time.sleep(0.05)  # 20 FPS
                
        except Exception as e:
            logger.error(f"Error during recording: {str(e)}")
        finally:
            if 'out' in locals():
                out.release() 