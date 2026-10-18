"""
Privacy Eye — Test Suite for Benchmark Forensic Analyzers
Tests FaceForensics++, Celeb-DF v2, MiniVision Silent-Face PAD, and FFHQ policy processor.
"""

import unittest
import numpy as np
import cv2

from app.ml.benchmarks import (
    FaceForensicsAnalyzer,
    CelebDFAnalyzer,
    SilentFaceAntiSpoofingEngine,
    FFHQPolicyProcessor,
)
from app.ml.live_authenticity import live_authenticity_engine


class TestBenchmarkForensics(unittest.TestCase):

    def setUp(self):
        # Create a synthetic face canvas for testing
        self.img = np.full((320, 320, 3), 130, dtype=np.uint8)
        # Face ellipse
        cv2.ellipse(self.img, (160, 160), (70, 90), 0, 0, 360, (180, 160, 140), -1)
        # Eyes
        cv2.circle(self.img, (130, 140), 12, (240, 240, 240), -1)
        cv2.circle(self.img, (130, 140), 5, (20, 20, 20), -1)
        cv2.circle(self.img, (132, 138), 2, (255, 255, 255), -1)  # Corneal glint
        cv2.circle(self.img, (190, 140), 12, (240, 240, 240), -1)
        cv2.circle(self.img, (190, 140), 5, (20, 20, 20), -1)
        cv2.circle(self.img, (192, 138), 2, (255, 255, 255), -1)  # Corneal glint
        # Nose & Mouth
        cv2.line(self.img, (160, 155), (160, 175), (100, 80, 70), 2)
        cv2.ellipse(self.img, (160, 205), (25, 10), 0, 0, 180, (80, 50, 60), -1)
        self.face_box = [90, 70, 140, 180]
        self.face_crop = self.img[70:250, 90:230]

    def test_faceforensics_analyzer(self):
        analyzer = FaceForensicsAnalyzer()
        res = analyzer.full_forensics_scan(self.face_crop, self.img)

        self.assertIn("faceforensics_score", res)
        self.assertIn("is_manipulated", res)
        self.assertIn("boundary", res)
        self.assertIn("color_consistency", res)
        self.assertIn("compression", res)
        self.assertGreaterEqual(res["faceforensics_score"], 0.0)
        self.assertLessEqual(res["faceforensics_score"], 1.0)

    def test_celeb_df_analyzer(self):
        analyzer = CelebDFAnalyzer()
        landmarks = np.array([
            [130, 140],  # right eye
            [190, 140],  # left eye
            [160, 170],  # nose
            [140, 205],  # right mouth
            [180, 205],  # left mouth
        ], dtype=np.float32)

        res = analyzer.full_celeb_scan(self.face_crop, landmarks)
        self.assertIn("celeb_df_score", res)
        self.assertIn("is_deepfake", res)
        self.assertIn("ocular_synthesis", res)
        self.assertIn("temporal_stability", res)

    def test_silent_face_pad_engine(self):
        engine = SilentFaceAntiSpoofingEngine()
        res = engine.full_silent_face_scan(self.img, self.face_box)

        self.assertIn("silent_face_spoof_score", res)
        self.assertIn("is_presentation_attack", res)
        self.assertIn("detected_attack_type", res)
        self.assertIn("scale_1_0_fourier", res)
        self.assertIn("scale_2_7_fourier", res)
        self.assertIn("scale_1_0_lbp", res)

    def test_ffhq_policy_and_texture_baseline(self):
        processor = FFHQPolicyProcessor()

        # Compliance checks
        compliant_meta = {"is_commercial": False, "is_biometric_id": False}
        comp_res = processor.verify_sample_compliance(compliant_meta)
        self.assertTrue(comp_res["compliant"])

        non_compliant_meta = {"is_commercial": True, "is_biometric_id": True}
        non_comp_res = processor.verify_sample_compliance(non_compliant_meta)
        self.assertFalse(non_comp_res["compliant"])
        self.assertEqual(len(non_comp_res["violations"]), 2)

        # Texture realism
        tex_res = processor.estimate_texture_realism(self.face_crop)
        self.assertIn("texture_realism_score", tex_res)
        self.assertIn("is_organic", tex_res)
        self.assertIn("has_corneal_glint", tex_res)
        self.assertTrue(tex_res["has_corneal_glint"])

    def test_live_authenticity_engine_benchmark_integration(self):
        from unittest.mock import patch
        _, buffer = cv2.imencode(".jpg", self.img)
        img_bytes = buffer.tobytes()

        mock_face = {
            "box": self.face_box,
            "landmarks": {
                "right_eye": [130, 140],
                "left_eye": [190, 140],
                "nose_tip": [160, 165],
                "right_mouth": [140, 205],
                "left_mouth": [180, 205],
            },
            "detector_confidence": 0.95,
        }
        with patch.object(live_authenticity_engine, "detect_face", return_value=mock_face):
            result = live_authenticity_engine.analyze_frame(
                img_bytes=img_bytes,
                session_id="test_benchmark_session",
                run_challenge=False,
            )

        self.assertIn("benchmarks", result)
        self.assertIn("faceforensics", result["benchmarks"])
        self.assertIn("celeb_df", result["benchmarks"])
        self.assertIn("silent_face", result["benchmarks"])
        self.assertIn("ffhq_baseline", result["benchmarks"])
        self.assertIn("confidence", result)
        self.assertIn("category_label", result)


if __name__ == "__main__":
    unittest.main()
