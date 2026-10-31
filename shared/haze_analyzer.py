"""
Haze analyzer with dual-camera input (IP RTSP / HDMI capture).

Public API:
    get_video_capture(settings) -> cv2.VideoCapture
    compute_haze_score(frame) -> float
    HazeMonitor(settings) — threading-based polling wrapper
"""

import os
import threading
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_OK = True
except Exception as e:  # pragma: no cover
    cv2 = None  # type: ignore
    CV2_OK = False
    logger.warning("opencv-python not installed: %s", e)

try:
    import numpy as np
    NP_OK = True
except Exception:  # pragma: no cover
    np = None  # type: ignore
    NP_OK = False


def get_video_capture(settings: dict) -> Optional[Any]:
    """
    Return a cv2.VideoCapture based on `settings`.

    settings expected keys:
        source_type: "IP RTSP" | "HDMI Capture" | "ip" | "hdmi"
        rtsp_url:    "rtsp://user:pass@host:554/stream"
        hdmi_index:  int (0, 1, 2)

    Returns None if cv2 missing or capture can't be opened.
    """
    if not CV2_OK:
        logger.error("OpenCV not available — cannot open camera.")
        return None

    settings = settings or {}
    stype = str(settings.get("source_type", "HDMI Capture")).lower()

    try:
        if "rtsp" in stype or stype == "ip":
            url = settings.get("rtsp_url", "") or ""
            if not url:
                logger.warning("IP RTSP selected but rtsp_url is empty.")
                return None
            logger.info("Opening RTSP capture: %s", url)
            cap = cv2.VideoCapture(url)
        else:
            index = int(settings.get("hdmi_index", 0) or 0)
            logger.info("Opening HDMI capture index: %d", index)
            cap = cv2.VideoCapture(index)

        if not cap or not cap.isOpened():
            logger.warning("Video capture failed to open.")
            return None
        return cap
    except Exception as e:
        logger.error("get_video_capture error: %s", e, exc_info=True)
        return None


def compute_haze_score(frame) -> float:
    """
    Haze Score = variance of the Laplacian of the grayscale frame.
    - Low  → blurry / hazy image (less detail)
    - High → sharp / clear image

    Returns 0.0 if the frame is invalid.
    """
    if not (CV2_OK and NP_OK):
        return 0.0
    if frame is None:
        return 0.0
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())
    except Exception as e:
        logger.error("compute_haze_score failed: %s", e)
        return 0.0


class HazeMonitor:
    """
    Poll a capture in a background thread, keep the latest haze score.
    Call start() once, then read `latest_score` / `is_hazy` properties.
    """

    def __init__(self, settings: dict, haze_threshold: float = 80.0,
                 fps: float = 5.0):
        self._settings = dict(settings or {})
        self._threshold = float(haze_threshold)
        self._interval = 1.0 / max(fps, 0.5)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._latest_score: float = 0.0
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="LightmanHazeMonitor", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def _run(self) -> None:
        cap = get_video_capture(self._settings)
        if cap is None:
            logger.warning("HazeMonitor: no capture available.")
            return
        try:
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok or frame is None:
                    self._stop.wait(self._interval)
                    continue
                score = compute_haze_score(frame)
                with self._lock:
                    self._latest_score = score
                self._stop.wait(self._interval)
        except Exception as e:
            logger.error("HazeMonitor loop error: %s", e, exc_info=True)
        finally:
            try:
                cap.release()
            except Exception:
                pass

    @property
    def latest_score(self) -> float:
        with self._lock:
            return self._latest_score

    @property
    def is_hazy(self) -> bool:
        return self.latest_score < self._threshold


def analyze_single_frame(settings: dict) -> float:
    """Grab one frame and return its haze score (blocking, quick)."""
    cap = get_video_capture(settings)
    if cap is None:
        return 0.0
    try:
        ok, frame = cap.read()
        if not ok or frame is None:
            return 0.0
        return compute_haze_score(frame)
    finally:
        try:
            cap.release()
        except Exception:
            pass