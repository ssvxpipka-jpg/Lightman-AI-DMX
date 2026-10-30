#!/usr/bin/env python3
"""
Lightman Haze / Smoke Analyzer
===============================

Estimates haze/smoke density in the stage area by analysing the IP-camera
feed.  When a hazer is active, light beams scatter through air particles,
creating visible volumetric lighting.  This module quantifies that
scattering to determine whether there is enough haze for beams to show.

Haze Score:
  0.0 = clear air (no scattering visible)
  1.0 = thick fog / heavy haze (strong scattering)

Algorithm:
  1. Project 3D fixture positions onto 2D image plane (orthographic).
  2. Extract beam regions using Canny edge detection + contrast analysis.
  3. Score = avg normalised edge density + beam brightness + contrast.

Usage:
    from shared.haze_analyzer import HazeAnalyzer
    analyzer = HazeAnalyzer()
    score = analyzer.analyze_frame(cv2_frame, fixture_positions_3d)
    if analyzer.should_warn_user(score):
        print("Increase hazer output!")
"""

from __future__ import annotations

from typing import List, Optional, Tuple

# Try to import numpy; fall back gracefully so the module loads without it
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    _HAS_NUMPY = False

# Try to import cv2; fall back gracefully so the module loads without OpenCV
try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    cv2 = None  # type: ignore
    _HAS_CV2 = False

from shared.config import get_logger

logger = get_logger("haze_analyzer")


class HazeAnalyzer:
    """
    Analyse IP-camera frames to estimate haze / smoke density for
    volumetric beam visibility.
    """

    DEFAULT_FOV_X = 60.0   # degrees horizontal
    DEFAULT_FOV_Y = 45.0   # degrees vertical
    DEFAULT_IMAGE_W = 640
    DEFAULT_IMAGE_H = 480
    STAGE_WIDTH = 200
    STAGE_DEPTH = 200

    def __init__(
        self,
        image_width: int = DEFAULT_IMAGE_W,
        image_height: int = DEFAULT_IMAGE_H,
        fov_x: float = DEFAULT_FOV_X,
        fov_y: float = DEFAULT_FOV_Y,
    ):
        self.image_w = image_width
        self.image_h = image_height
        self.fov_x = fov_x
        self.fov_y = fov_y
        self._beam_regions: List[Tuple[int, int, int, int]] = []

    def world_to_image(self, point: Tuple[float, float, float]) -> Tuple[int, int]:
        """
        Project a 3D world point (x, y, z) to 2D image coords (u, v).
        Uses a simplified orthographic projection: camera is above
        and behind the stage, looking down at a 45-degree angle.
        X maps to u, Z maps to v, Y (height) is ignored.
        """
        x, y, z = point
        nx = x / (self.STAGE_WIDTH / 2)
        nz = z / (self.STAGE_DEPTH / 2)
        u = int((nx + 1) * self.image_w / 2)
        v = int((1 - nz) * self.image_h / 2)
        u = max(0, min(self.image_w - 1, u))
        v = max(0, min(self.image_h - 1, v))
        return u, v

    def compute_beam_regions(
        self, fixture_positions_3d: List[Tuple[float, float, float]]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Project fixture positions and stage centre to compute 2D
        line regions where beams are expected.
        Returns list of (x, y, w, h) bounding boxes.
        """
        stage_centre = (0.0, 0.0, 0.0)
        stage_cu, stage_cv = self.world_to_image(stage_centre)
        regions = []

        for pos in fixture_positions_3d:
            fu, fv = self.world_to_image(pos)
            x1 = min(fu, stage_cu)
            x2 = max(fu, stage_cu)
            y1 = min(fv, stage_cv)
            y2 = max(fv, stage_cv)
            thickness = 30
            x1 = max(0, x1 - thickness)
            x2 = min(self.image_w, x2 + thickness)
            y1 = max(0, y1 - thickness)
            y2 = min(self.image_h, y2 + thickness)
            if x2 - x1 > 5 and y2 - y1 > 5:
                regions.append((x1, y1, x2 - x1, y2 - y1))

        self._beam_regions = regions
        return regions

    def analyze_frame(
        self, cv2_frame: np.ndarray,
        fixture_positions_3d: List[Tuple[float, float, float]]
    ) -> float:
        """
        Analyse a camera frame and return a Haze Score (0.0 - 1.0).
        0.0 = no haze, 1.0 = thick fog.
        """
        if not _HAS_CV2 or cv2 is None:
            logger.warning("OpenCV (cv2) not available — returning 0.0")
            return 0.0

        if not _HAS_NUMPY or np is None:
            logger.warning("NumPy not available — returning 0.0")
            return 0.0

        if cv2_frame is None or cv2_frame.size == 0:
            logger.warning("Empty frame — returning 0.0")
            return 0.0

        h, w = cv2_frame.shape[:2]
        if (w, h) != (self.image_w, self.image_h):
            self.image_w, self.image_h = w, h

        regions = self.compute_beam_regions(fixture_positions_3d)
        if not regions:
            logger.info("No beam regions — returning 0.0")
            return 0.0

        # Convert to grayscale
        gray = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2GRAY)

        # Canny edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Overall brightness
        mean_brightness = float(np.mean(gray)) / 255.0

        beam_scores = []
        for (x, y, rw, rh) in regions:
            if rw <= 0 or rh <= 0:
                continue
            roi_gray = gray[y:y + rh, x:x + rw]
            roi_edges = edges[y:y + rh, x:x + rw]
            if roi_gray.size == 0 or roi_edges.size == 0:
                continue

            # Edge density (visible beam edges)
            edge_density = float(np.count_nonzero(roi_edges)) / float(roi_edges.size)

            # Beam brightness
            beam_brightness = float(np.mean(roi_gray)) / 255.0

            # Contrast (scattering indicator)
            if roi_gray.std() > 0:
                contrast = float(roi_gray.std()) / 255.0
            else:
                contrast = 0.0

            # Combined score
            region_score = (
                edge_density * 0.4 +
                beam_brightness * 0.4 +
                contrast * 0.2
            )
            beam_scores.append(min(region_score, 1.0))

        if not beam_scores:
            return 0.0

        haze_score = float(np.mean(beam_scores))

        # Boost if ambient is dark (beams more visible)
        if mean_brightness < 0.3 and haze_score > 0.05:
            haze_score = min(haze_score * 1.2, 1.0)

        haze_score = max(0.0, min(1.0, haze_score))

        logger.debug(
            f"Haze: {len(regions)} regions, brightness={mean_brightness:.3f}, "
            f"score={haze_score:.3f}"
        )
        return haze_score

    def should_warn_user(self, score: float, min_acceptable: float = 0.3) -> bool:
        """
        Return True if the haze score is below the minimum acceptable threshold.
        A low score means beams are barely visible — add haze.
        """
        return score < min_acceptable

    def analyze_frame_from_capture(
        self,
        cap: object,
        fixture_positions_3d: List[Tuple[float, float, float]],
    ) -> Optional[float]:
        """
        Grab a frame from a cv2.VideoCapture and analyse it.
        Returns the haze score, or None if the frame couldn't be read.
        """
        if not _HAS_CV2:
            return None

        ret, frame = cap.read()
        if not ret or frame is None:
            logger.warning("Could not read frame from capture")
            return None

        return self.analyze_frame(frame, fixture_positions_3d)

    def get_frame_size(self, cap: object) -> Tuple[int, int]:
        """Return (width, height) of the video capture."""
        if not _HAS_CV2:
            return self.DEFAULT_IMAGE_W, self.DEFAULT_IMAGE_H

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return w, h