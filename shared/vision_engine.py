"""Lightman Vision Engine — EpocCam input with haze analysis and object tracking.

Public API:
    get_video_capture(settings) -> cv2.VideoCapture
    compute_haze_score(frame) -> float
    HazeMonitor(settings) — threading-based polling wrapper
    analyze_single_frame(settings) -> float
"""

from shared.haze_analyzer import (  # noqa: F401
    get_video_capture,
    compute_haze_score,
    HazeMonitor,
    analyze_single_frame,
)