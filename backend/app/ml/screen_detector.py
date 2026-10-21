"""
Privacy Eye — Screen, Phone & Presentation Attack Detection Engine
Differentiates between a phone present elsewhere in the scene (Case A: human holding phone)
versus a phone/screen physically displaying the target face (Case B: presentation attack).
"""
import math
import numpy as np
import cv2
from typing import Dict, Any, List, Optional, Tuple


class ScreenDetector:
    """
    Multimodal Display & Presentation Attack Detector.
    Evaluates geometric rectangular bezels, Moiré frequency harmonics,
    specular display reflections, perimeter bezel margins, and screen-to-face spatial association.
    """

    def __init__(self, attack_threshold: float = 0.55):
        self.attack_threshold = attack_threshold

    def detect_display_bezels(
        self, img_bgr: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Detects rectangular smartphone, tablet, laptop, or monitor screens in the frame
        using multi-scale edge contours, convex hull bridging (for handheld phones),
        polygon approximation, and aspect-ratio filters.
        """
        h, w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # Bilateral filter preserves sharp screen bezel edges while smoothing interior textures
        blurred = cv2.bilateralFilter(gray, 7, 50, 50)
        detected_screens = []

        min_screen_area = (w * h) * 0.03   # Screen must occupy at least 3% of frame
        max_screen_area = (w * h) * 0.98

        # Multi-scale edge thresholds for varying lighting environments
        for canny_lo, canny_hi in [(30, 100), (20, 80)]:
            edges = cv2.Canny(blurred, canny_lo, canny_hi)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(edges, kernel, iterations=1)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                # Test both raw contour and convex hull
                # (Convex hull bridges user fingers/hands gripping phone bezels and rounded screen corners)
                for c in [cnt, cv2.convexHull(cnt)]:
                    area = cv2.contourArea(c)
                    if area < min_screen_area or area > max_screen_area:
                        continue

                    peri = cv2.arcLength(c, True)
                    # Multi-scale polygon approximation
                    for eps in [0.035, 0.05]:
                        approx = cv2.approxPolyDP(c, eps * peri, True)

                        # Screens are quadrilateral or convex polygons (4-6 vertices to allow hand grip/curved bezels)
                        if len(approx) in (4, 5, 6) and cv2.isContourConvex(approx):
                            bx, by, bw, bh = cv2.boundingRect(approx)
                            aspect = float(bw) / float(bh) if bh > 0 else 1.0

                            # Smartphone, tablet, laptop, monitor (aspect ratio 0.35 to 2.85)
                            is_display_aspect = (0.35 <= aspect <= 2.85)
                            if not is_display_aspect:
                                continue

                            # Calculate screen confidence based on geometric rectangularity
                            rect_area = bw * bh
                            extent = float(area) / float(rect_area) if rect_area > 0 else 0.0
                            if extent < 0.65:
                                continue

                            device_type = "SMARTPHONE" if (0.38 <= aspect <= 0.85 or 1.25 <= aspect <= 2.65) else "SCREEN_OR_TABLET"
                            screen_conf = min(0.98, round(0.65 + (extent * 0.25) + min(0.10, area / (w * h)), 2))

                            detected_screens.append({
                                "box": [bx, by, bw, bh],
                                "polygon": approx.tolist(),
                                "device_type": device_type,
                                "confidence": screen_conf,
                                "aspect_ratio": round(aspect, 2),
                                "area_pct": round((area / (w * h)) * 100.0, 1),
                            })

        # Non-maximum suppression by bounding box IoU
        detected_screens = self._nms_screens(detected_screens)
        return detected_screens

    def _nms_screens(self, screens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(screens) <= 1:
            return screens
        screens = sorted(screens, key=lambda s: s["confidence"], reverse=True)
        keep = []
        for s in screens:
            box_a = s["box"]
            overlap = False
            for k in keep:
                box_b = k["box"]
                iou = self.calculate_iou(box_a, box_b)
                if iou > 0.45:
                    overlap = True
                    break
            if not overlap:
                keep.append(s)
        return keep

    @staticmethod
    def calculate_iou(box_a: List[int], box_b: List[int]) -> float:
        xa = max(box_a[0], box_b[0])
        ya = max(box_a[1], box_b[1])
        xb = min(box_a[0] + box_a[2], box_b[0] + box_b[2])
        yb = min(box_a[1] + box_a[3], box_b[1] + box_b[3])
        inter = max(0, xb - xa) * max(0, yb - ya)
        area_a = box_a[2] * box_a[3]
        area_b = box_b[2] * box_b[3]
        union = area_a + area_b - inter
        return float(inter / union) if union > 0 else 0.0

    @staticmethod
    def calculate_iof(face_box: List[int], screen_box: List[int]) -> float:
        """
        Intersection-over-Face (IoF): what percentage of the face is inside the screen.
        """
        fx, fy, fw, fh = face_box
        sx, sy, sw, sh = screen_box

        xa = max(fx, sx)
        ya = max(fy, sy)
        xb = min(fx + fw, sx + sw)
        yb = min(fy + fh, sy + sh)

        inter = max(0, xb - xa) * max(0, yb - ya)
        face_area = fw * fh
        return float(inter / face_area) if face_area > 0 else 0.0

    def scan_face_perimeter_bezel(
        self, img_bgr: np.ndarray, face_box: List[int]
    ) -> Dict[str, Any]:
        """
        Directly scans the margin collar flanking the face for physical smartphone/screen bezels.
        Detects parallel vertical edges (Hough line segments) and sharp gradient step discontinuities.
        """
        if not face_box:
            return {"has_bezel_lines": False, "vertical_lines": 0, "edge_energy": 0.0}

        fx, fy, fw, fh = face_box
        h, w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        pad_w = int(fw * 0.45)
        pad_h = int(fh * 0.35)
        collar = gray[max(0, fy - pad_h) : min(h, fy + fh + pad_h), max(0, fx - pad_w) : min(w, fx + fw + pad_w)]
        if collar.size == 0:
            return {"has_bezel_lines": False, "vertical_lines": 0, "edge_energy": 0.0}

        edges = cv2.Canny(collar, 30, 90)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=35, minLineLength=int(fh * 0.35), maxLineGap=12)

        vertical_lines = 0
        horizontal_lines = 0
        if lines is not None:
            for lx1, ly1, lx2, ly2 in lines.reshape(-1, 4):
                ang = np.degrees(np.arctan2(abs(ly2 - ly1), abs(lx2 - lx1)))
                if 75 <= ang <= 105:
                    vertical_lines += 1
                elif ang <= 15 or ang >= 165:
                    horizontal_lines += 1

        # Sobel vertical energy on left and right perimeter boundary strips
        left_strip = gray[max(0, fy) : min(h, fy + fh), max(0, fx - int(fw * 0.4)) : fx]
        right_strip = gray[max(0, fy) : min(h, fy + fh), fx + fw : min(w, fx + fw + int(fw * 0.4))]
        left_e = float(np.mean(np.abs(cv2.Sobel(left_strip, cv2.CV_64F, 1, 0, ksize=3)))) if left_strip.size > 0 else 0.0
        right_e = float(np.mean(np.abs(cv2.Sobel(right_strip, cv2.CV_64F, 1, 0, ksize=3)))) if right_strip.size > 0 else 0.0
        avg_e = (left_e + right_e) / 2.0

        # Physical bezel signature: vertical straight edges bounding both sides with significant gradient energy
        has_bezel = (vertical_lines >= 4 and avg_e > 25.0) or (vertical_lines >= 8)
        return {
            "has_bezel_lines": has_bezel,
            "vertical_lines": vertical_lines,
            "horizontal_lines": horizontal_lines,
            "edge_energy": round(avg_e, 1),
        }

    def compute_moire_and_specular_signals(
        self, face_crop_bgr: np.ndarray
    ) -> Dict[str, float]:
        """
        Computes 2D FFT Moiré high-frequency grid energy and specular reflection spikes.
        Evaluates Green channel primarily where OLED PenTile and LCD subpixel rasterization is strongest.
        """
        if face_crop_bgr.shape[0] < 30 or face_crop_bgr.shape[1] < 30:
            return {"moire_score": 0.0, "specular_score": 0.0}

        # Green channel has 2x Bayer subpixel density and captures OLED/LCD subpixel grid most accurately
        b, g, r = cv2.split(face_crop_bgr)
        h, w = g.shape[:2]

        # 1. 2D FFT for periodic screen subpixel patterns
        f = np.fft.fft2(g.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1.0)

        # Sample high-frequency outer perimeter
        cy, cx = h // 2, w // 2
        r_inner = int(min(cy, cx) * 0.40)
        y, x = np.ogrid[:h, :w]
        mask_outer = ((x - cx) ** 2 + (y - cy) ** 2) >= (r_inner ** 2)

        hf_mean = float(np.mean(magnitude[mask_outer]))
        lf_mean = float(np.mean(magnitude[~mask_outer]))
        ratio = hf_mean / max(lf_mean, 1.0)
        # Ratio typically ~0.35-0.55 for natural skin, >= 0.70 for digital screens
        moire_score = max(0.0, min(1.0, (ratio - 0.45) / 0.35))

        # 2. Specular glass reflections (harsh saturated white glare spots on display glass)
        hsv = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2HSV)
        val = hsv[:, :, 2]
        sat = hsv[:, :, 1]
        glare_pixels = (val > 245) & (sat < 35)
        glare_ratio = float(np.mean(glare_pixels))
        specular_score = max(0.0, min(1.0, glare_ratio * 25.0))

        return {
            "moire_score": round(moire_score, 3),
            "specular_score": round(specular_score, 3),
        }

    def analyze(
        self,
        img_bgr: np.ndarray,
        face_box: Optional[List[int]],
        temporal_jitter: float = 1.0,
        is_liveness_proven: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes screen detection, screen-face association, and presentation attack scoring.
        Supports active liveness override (head turning & regular blinking disproves replay attacks).
        """
        screens = self.detect_display_bezels(img_bgr)
        phone_in_scene = len(screens) > 0

        if not face_box:
            return {
                "phone_detected": phone_in_scene,
                "screen_face_associated": False,
                "presentation_attack": False,
                "phone_object_confidence": max([s["confidence"] for s in screens], default=0.0),
                "screen_face_association_confidence": 0.0,
                "presentation_attack_confidence": 0.0,
                "associated_screen": None,
                "detected_screens": screens,
                "reason_codes": ["PHONE_DETECTED"] if phone_in_scene else [],
                "user_message": "Mobile device present in scene" if phone_in_scene else None,
            }

        fx, fy, fw, fh = face_box
        fcx, fcy = fx + fw // 2, fy + fh // 2
        face_crop = img_bgr[fy : fy + fh, fx : fx + fw]
        signals = self.compute_moire_and_specular_signals(face_crop)
        bezel_info = self.scan_face_perimeter_bezel(img_bgr, face_box)

        best_associated_screen = None
        max_iof = 0.0
        center_inside_screen = False

        for s in screens:
            iof = self.calculate_iof(face_box, s["box"])
            bx, by, bw, bh = s["box"]
            is_center_in = (bx <= fcx <= bx + bw and by <= fcy <= by + bh)
            if iof > max_iof:
                max_iof = iof
                best_associated_screen = s
                center_inside_screen = is_center_in

        # Face containment: IoF >= 0.50 OR center of face inside detected screen with IoF >= 0.35
        face_inside_screen = bool(max_iof >= 0.50 or (center_inside_screen and max_iof >= 0.35))
        has_perimeter_bezel = bezel_info["has_bezel_lines"]

        screen_conf = best_associated_screen["confidence"] if best_associated_screen else (0.85 if has_perimeter_bezel else 0.0)
        assoc_conf = round(float(max_iof), 2)

        # Distinguish large background wall displays (e.g., room TV / desktop monitor behind subject)
        is_background_display = False
        if best_associated_screen:
            s_box = best_associated_screen["box"]
            screen_area = s_box[2] * s_box[3]
            face_area = fw * fh
            area_ratio = float(screen_area / max(face_area, 1))
            if area_ratio > 4.5 and signals["moire_score"] < 0.60:
                is_background_display = True

        reason_codes = []
        user_message = None

        # Presentation Attack Confidence Logic
        if is_liveness_proven:
            # Active 3D head rotation and regular physiological blinking prove bona fide live human
            is_attack = False
            presentation_attack_confidence = 0.0
            if phone_in_scene:
                reason_codes.append("BACKGROUND_SCREEN_NON_ATTACK")
                user_message = "Background display detected; live active human presence verified."
        elif is_background_display:
            is_attack = False
            presentation_attack_confidence = 0.0
            reason_codes.append("BACKGROUND_SCREEN_NON_ATTACK")
            user_message = "Background monitor/TV detected; face in front of screen."
        elif face_inside_screen:
            # Physical containment inside detected handheld device bezel
            geo_evidence = (screen_conf * 0.45) + (assoc_conf * 0.45)
            artifact_boost = (signals["moire_score"] * 0.10) + (signals["specular_score"] * 0.10)
            if has_perimeter_bezel:
                artifact_boost += 0.10
            phys_evidence = min(0.99, max(0.80, geo_evidence + artifact_boost))

            if temporal_jitter < 0.20:
                phys_evidence = min(1.0, phys_evidence + 0.10)

            presentation_attack_confidence = round(float(min(0.99, phys_evidence)), 2)
            is_attack = True
            reason_codes.append("PHONE_PRESENTATION_DETECTED")
            reason_codes.append("SCREEN_FACE_DETECTED")
            user_message = "A face appears to be displayed through a phone or electronic screen."
        elif has_perimeter_bezel and signals["moire_score"] >= 0.45:
            # Device bezel directly framing the face combined with screen subpixel Moiré pattern
            is_attack = True
            presentation_attack_confidence = min(0.98, round(0.70 + (signals["moire_score"] * 0.25) + (signals["specular_score"] * 0.10), 2))
            reason_codes.append("PHONE_PRESENTATION_DETECTED")
            reason_codes.append("SCREEN_FACE_DETECTED")
            user_message = "A face appears to be displayed through a phone or electronic screen."
        elif signals["moire_score"] >= 0.85 and signals["specular_score"] >= 0.25:
            # Harsh planar glass glare and intense screen frequency grid directly over the face
            is_attack = True
            presentation_attack_confidence = min(0.92, round(0.75 + (signals["moire_score"] * 0.15), 2))
            reason_codes.append("PHONE_PRESENTATION_DETECTED")
            reason_codes.append("SCREEN_FACE_DETECTED")
            user_message = "A face appears to be displayed through a phone or electronic screen."
        else:
            # Case A: Phone is in scene, but face is NOT inside phone!
            presentation_attack_confidence = round(float(signals["moire_score"] * 0.20), 2)
            is_attack = False
            if phone_in_scene:
                reason_codes.append("PHONE_IN_SCENE_IRRELEVANT")
                user_message = "Electronic device detected in scene (Direct human face verified)."

        return {
            "phone_detected": phone_in_scene or has_perimeter_bezel,
            "screen_face_associated": face_inside_screen or has_perimeter_bezel,
            "presentation_attack": is_attack,
            "phone_object_confidence": screen_conf,
            "screen_face_association_confidence": assoc_conf,
            "presentation_attack_confidence": presentation_attack_confidence,
            "moire_score": signals["moire_score"],
            "specular_score": signals["specular_score"],
            "associated_screen": best_associated_screen,
            "detected_screens": screens,
            "reason_codes": reason_codes,
            "user_message": user_message,
        }


# Global singleton instance
screen_detector = ScreenDetector()
