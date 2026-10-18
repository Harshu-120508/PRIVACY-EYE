"""
Privacy Eye — Dedicated Eye Analysis & Visibility Module
Performs eye landmark localization, ocular patch extraction, sharpness & contrast scoring,
occlusion/sunglasses discrimination, and calibrated visibility state classification.
"""
import math
import numpy as np
import cv2
from typing import Dict, Any, List, Optional, Tuple

# Eye Visibility States
BOTH_EYES_VISIBLE = "BOTH_EYES_VISIBLE"
LEFT_ONLY = "LEFT_ONLY"
RIGHT_ONLY = "RIGHT_ONLY"
BOTH_EYES_NOT_VISIBLE = "BOTH_EYES_NOT_VISIBLE"
EYE_PARTIALLY_OCCLUDED = "EYE_PARTIALLY_OCCLUDED"
EYE_TOO_BLURRY = "EYE_TOO_BLURRY"
EYE_OUT_OF_FRAME = "EYE_OUT_OF_FRAME"
EYE_TOO_SMALL = "EYE_TOO_SMALL"
EYES_OBSCURED = "EYES_OBSCURED"


class EyeAnalyzer:
    """
    Dedicated Eye Analysis Engine for live biometric authenticity.
    Evaluates left and right eye quality independently without assuming symmetry.
    """

    def __init__(self, min_blur_var: float = 12.0, min_eye_size_px: int = 8):
        self.min_blur_var = min_blur_var
        self.min_eye_size_px = min_eye_size_px

    def extract_eye_orbit(
        self,
        img_bgr: np.ndarray,
        eye_pt: List[int],
        iod: float,
        is_left_eye: bool,
    ) -> Tuple[Optional[np.ndarray], List[int]]:
        """
        Extracts anatomical eye orbit patch around pupil center using interocular distance (IOD).
        Returns cropped BGR patch and [x, y, w, h] bounding box.
        """
        h, w = img_bgr.shape[:2]
        ex, ey = int(eye_pt[0]), int(eye_pt[1])

        # Width ~ 0.36 of IOD, Height ~ 0.26 of IOD
        half_w = max(self.min_eye_size_px, int(iod * 0.18))
        half_h = max(self.min_eye_size_px - 2, int(iod * 0.13))

        x1 = max(0, ex - half_w)
        y1 = max(0, ey - half_h)
        x2 = min(w, ex + half_w)
        y2 = min(h, ey + half_h)

        if (x2 - x1) < self.min_eye_size_px or (y2 - y1) < (self.min_eye_size_px - 4):
            return None, [x1, y1, max(0, x2 - x1), max(0, y2 - y1)]

        crop = img_bgr[y1:y2, x1:x2]
        return crop, [x1, y1, x2 - x1, y2 - y1]

    def evaluate_patch_quality(
        self, patch_bgr: np.ndarray
    ) -> Dict[str, Any]:
        """
        Calculates sharpness, contrast, illumination, and occlusion for an ocular crop.
        """
        gray = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        # 1. Laplacian variance for sharpness
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = float(lap.var())
        is_sharp = lap_var >= self.min_blur_var

        # 2. Contrast & Dynamic Range
        contrast = float(np.std(gray))
        min_v, max_v = float(np.min(gray)), float(np.max(gray))
        dynamic_range = max_v - min_v

        # 3. Illumination & Glare
        mean_lum = float(np.mean(gray))
        is_dark = mean_lum < 30.0
        is_glare = float(np.mean(gray > 240)) > 0.15

        # 4. Sunglasses / Dark obstruction check
        hsv = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2HSV)
        sat_mean = float(np.mean(hsv[:, :, 1]))
        val_mean = float(np.mean(hsv[:, :, 2]))
        # Polarized/dark lenses: low luminance, low saturation, lack of sclera gradients
        is_sunglasses = (val_mean < 45.0 and sat_mean < 40.0) or (mean_lum < 50.0 and dynamic_range < 35.0)

        # 5. Openness estimation: vertical Sobel energy + contrast + pupil contrast
        sob_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        vert_energy = float(np.mean(np.abs(sob_y)))
        min_10 = float(np.percentile(gray, 10))
        pupil_contrast = max(0.0, mean_lum - min_10)
        openness_score = (vert_energy * 0.45) + (contrast * 0.25) + (pupil_contrast * 0.30)

        # Calibrated 0.0 to 1.0 quality score
        q_sharp = min(1.0, lap_var / 80.0)
        q_contrast = min(1.0, contrast / 35.0)
        q_illum = 1.0 - (0.6 if is_dark else 0.0) - (0.4 if is_glare else 0.0)

        quality_score = max(0.0, min(1.0, (q_sharp * 0.45) + (q_contrast * 0.35) + (q_illum * 0.20)))
        if is_sunglasses:
            quality_score = min(quality_score, 0.20)

        return {
            "lap_var": round(lap_var, 1),
            "is_sharp": is_sharp,
            "contrast": round(contrast, 1),
            "mean_lum": round(mean_lum, 1),
            "is_dark": is_dark,
            "is_glare": is_glare,
            "is_sunglasses": is_sunglasses,
            "openness": round(openness_score, 2),
            "quality": round(quality_score, 2),
        }

    def analyze(
        self,
        img_bgr: np.ndarray,
        landmarks: Optional[Dict[str, List[int]]],
        face_box: Optional[List[int]],
        head_yaw: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Executes full eye detection, quality assessment, and state determination.
        """
        user_guidance = []
        reason_codes = []

        if not landmarks or not face_box:
            return {
                "eye_status": BOTH_EYES_NOT_VISIBLE,
                "left_eye_visible": False,
                "right_eye_visible": False,
                "left_eye_quality": 0.0,
                "right_eye_quality": 0.0,
                "overall_eye_quality": 0.0,
                "eye_visibility_score": 0.0,
                "openness": 0.0,
                "is_blurry": False,
                "is_obscured": False,
                "left_eye_box": None,
                "right_eye_box": None,
                "reason_codes": ["EYES_NOT_VISIBLE"],
                "user_guidance": ["Position face inside frame to align eyes"],
            }

        re_pt = landmarks.get("right_eye")
        le_pt = landmarks.get("left_eye")
        if not re_pt or not le_pt:
            return {
                "eye_status": BOTH_EYES_NOT_VISIBLE,
                "left_eye_visible": False,
                "right_eye_visible": False,
                "left_eye_quality": 0.0,
                "right_eye_quality": 0.0,
                "overall_eye_quality": 0.0,
                "eye_visibility_score": 0.0,
                "openness": 0.0,
                "is_blurry": False,
                "is_obscured": False,
                "left_eye_box": None,
                "right_eye_box": None,
                "reason_codes": ["EYES_NOT_VISIBLE"],
                "user_guidance": ["Eyes not detected in face contour"],
            }

        iod = max(10.0, float(math.hypot(le_pt[0] - re_pt[0], le_pt[1] - re_pt[1])))

        # Extract eye crops
        # Note: in computer vision convention, left_eye is image viewer's left or subject's left
        right_crop, right_box = self.extract_eye_orbit(img_bgr, re_pt, iod, is_left_eye=False)
        left_crop, left_box = self.extract_eye_orbit(img_bgr, le_pt, iod, is_left_eye=True)

        if right_crop is None or left_crop is None:
            status = EYE_TOO_SMALL if iod < 25.0 else EYE_OUT_OF_FRAME
            return {
                "eye_status": status,
                "left_eye_visible": left_crop is not None,
                "right_eye_visible": right_crop is not None,
                "left_eye_quality": 0.1,
                "right_eye_quality": 0.1,
                "overall_eye_quality": 0.1,
                "eye_visibility_score": 0.25,
                "openness": 10.0,
                "is_blurry": True,
                "is_obscured": False,
                "left_eye_box": left_box,
                "right_eye_box": right_box,
                "reason_codes": ["EYES_TOO_BLURRY", "EYE_SIGNAL_UNAVAILABLE"],
                "user_guidance": ["Move closer to camera: eyes too small or clipped"],
            }

        # Quality measurements
        q_right = self.evaluate_patch_quality(right_crop)
        q_left = self.evaluate_patch_quality(left_crop)

        left_sharp = q_left["is_sharp"]
        right_sharp = q_right["is_sharp"]
        is_blurry = not (left_sharp or right_sharp)
        is_obscured = q_left["is_sunglasses"] or q_right["is_sunglasses"]

        left_vis = q_left["quality"] >= 0.40 and not q_left["is_sunglasses"]
        right_vis = q_right["quality"] >= 0.40 and not q_right["is_sunglasses"]

        # Handle head yaw hiding one eye
        if head_yaw < -0.25:
            # Turned right: right eye partially obscured by bridge
            right_vis = False
        elif head_yaw > +0.25:
            # Turned left: left eye partially obscured
            left_vis = False

        # Classify overall eye status
        if is_obscured:
            eye_status = EYES_OBSCURED
            eye_visibility_score = 0.0
            reason_codes.append("EYE_SIGNAL_UNAVAILABLE")
            user_guidance.append("Eyes obscured by dark lenses or accessories; eye liveness unavailable")
        elif is_blurry:
            eye_status = EYE_TOO_BLURRY
            eye_visibility_score = 0.25
            reason_codes.append("EYES_TOO_BLURRY")
            user_guidance.append("Eyes not clearly visible due to motion blur; hold camera steady")
        elif left_vis and right_vis:
            eye_status = BOTH_EYES_VISIBLE
            eye_visibility_score = 1.0
        elif left_vis and not right_vis:
            eye_status = LEFT_ONLY
            eye_visibility_score = 0.70
            user_guidance.append("Left eye clear; right eye partially turned or shadowed")
        elif right_vis and not left_vis:
            eye_status = RIGHT_ONLY
            eye_visibility_score = 0.70
            user_guidance.append("Right eye clear; left eye partially turned or shadowed")
        else:
            eye_status = BOTH_EYES_NOT_VISIBLE
            eye_visibility_score = 0.0
            reason_codes.append("EYES_NOT_VISIBLE")
            user_guidance.append("Eyes not clearly visible; improve lighting and face camera")

        overall_quality = round((q_left["quality"] + q_right["quality"]) / 2.0, 2)
        mean_openness = round((q_left["openness"] + q_right["openness"]) / 2.0, 2)

        return {
            "eye_status": eye_status,
            "left_eye_visible": bool(left_vis),
            "right_eye_visible": bool(right_vis),
            "left_eye_quality": float(q_left["quality"]),
            "right_eye_quality": float(q_right["quality"]),
            "overall_eye_quality": float(overall_quality),
            "eye_visibility_score": float(eye_visibility_score),
            "openness": float(mean_openness),
            "is_blurry": bool(is_blurry),
            "is_obscured": bool(is_obscured),
            "left_eye_box": left_box,
            "right_eye_box": right_box,
            "reason_codes": reason_codes,
            "user_guidance": user_guidance,
        }
