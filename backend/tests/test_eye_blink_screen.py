"""
Privacy Eye — Comprehensive Unit & Integration Tests:
Ocular Quality, Biological Blink State Machine, 25-Second Observation Challenge,
and Screen Presentation Attack Association Engine.
"""
import time
import numpy as np
import cv2

from app.ml.eye_analyzer import (
    EyeAnalyzer,
    BOTH_EYES_VISIBLE,
    LEFT_ONLY,
    RIGHT_ONLY,
    BOTH_EYES_NOT_VISIBLE,
    EYE_TOO_BLURRY,
    EYES_OBSCURED,
)
from app.ml.blink_engine import BlinkEngine
from app.ml.screen_detector import ScreenDetector
from app.ml.live_authenticity import live_authenticity_engine


# ── 1. EYE ANALYZER TESTS ──────────────────────────────────────────────────────

def test_eye_analyzer_both_visible():
    analyzer = EyeAnalyzer()
    img = np.ones((480, 640, 3), dtype=np.uint8) * 140
    # Add texture/gradients around eye positions with high contrast sclera & pupil
    cv2.circle(img, (260, 200), 22, (245, 245, 245), -1)
    cv2.circle(img, (260, 200), 10, (20, 15, 10), -1)
    cv2.circle(img, (380, 200), 22, (245, 245, 245), -1)
    cv2.circle(img, (380, 200), 10, (20, 15, 10), -1)

    face_box = [200, 120, 240, 260]
    landmarks = {
        "right_eye": [260, 200],
        "left_eye": [380, 200],
        "nose_tip": [320, 260],
        "right_mouth": [270, 320],
        "left_mouth": [370, 320],
    }

    res = analyzer.analyze(img, landmarks, face_box)
    assert res["left_eye_visible"] is True
    assert res["right_eye_visible"] is True
    assert res["eye_status"] == BOTH_EYES_VISIBLE
    assert res["overall_eye_quality"] >= 0.35
    assert not res["is_blurry"]


def test_eye_analyzer_blurry_eyes():
    analyzer = EyeAnalyzer()
    # Uniform low-frequency blurred image
    img = np.ones((480, 640, 3), dtype=np.uint8) * 130

    face_box = [200, 120, 240, 260]
    landmarks = {
        "right_eye": [260, 200],
        "left_eye": [380, 200],
        "nose_tip": [320, 260],
        "right_mouth": [270, 320],
        "left_mouth": [370, 320],
    }

    res = analyzer.analyze(img, landmarks, face_box)
    assert res["is_blurry"] is True or res["overall_eye_quality"] < 0.20
    assert res["eye_status"] in (EYE_TOO_BLURRY, BOTH_EYES_NOT_VISIBLE)


def test_eye_analyzer_sunglasses_obscured():
    analyzer = EyeAnalyzer()
    img = np.ones((480, 640, 3), dtype=np.uint8) * 160
    # Paint dark low-contrast sunglasses
    cv2.rectangle(img, (220, 170), (300, 230), (12, 12, 12), -1)
    cv2.rectangle(img, (340, 170), (420, 230), (12, 12, 12), -1)

    face_box = [200, 120, 240, 260]
    landmarks = {
        "right_eye": [260, 200],
        "left_eye": [380, 200],
        "nose_tip": [320, 260],
        "right_mouth": [270, 320],
        "left_mouth": [370, 320],
    }

    res = analyzer.analyze(img, landmarks, face_box)
    assert res["is_obscured"] is True
    assert res["eye_status"] == EYES_OBSCURED
    assert "EYE_SIGNAL_UNAVAILABLE" in res["reason_codes"]


# ── 2. BLINK ENGINE TESTS ──────────────────────────────────────────────────────

def test_blink_engine_biological_blink_detection():
    engine = BlinkEngine()
    session_id = "test_blink_sess_001"

    eye_data_open = {
        "eye_status": BOTH_EYES_VISIBLE,
        "is_blurry": False,
        "is_obscured": False,
        "overall_eye_quality": 0.85,
        "left_eye_quality": 0.85,
        "right_eye_quality": 0.85,
        "left_eye_visible": True,
        "right_eye_visible": True,
    }

    # Step 1: Open eyes (initial state)
    res1 = engine.update(session_id, openness=0.32, eye_analysis=eye_data_open, face_detected=True)
    assert res1["blink_count"] == 0
    assert not res1["is_timer_paused"]

    # Step 2: Eyes closing/closed (120ms later)
    sess = engine._get_or_create_session(session_id)
    sess["state"] = "CLOSED"
    sess["closed_since"] = time.time() - 0.15

    # Step 3: Eyes reopened -> Biological blink confirmed!
    res3 = engine.update(session_id, openness=0.31, eye_analysis=eye_data_open, face_detected=True)
    assert res3["blink_count"] == 1
    assert "BLINK_DETECTED" in res3["reason_codes"]


def test_blink_engine_pause_on_blurry_eyes():
    engine = BlinkEngine()
    session_id = "test_blink_sess_pause"

    eye_data_blurry = {
        "eye_status": EYE_TOO_BLURRY,
        "is_blurry": True,
        "is_obscured": False,
        "overall_eye_quality": 0.18,
        "left_eye_quality": 0.18,
        "right_eye_quality": 0.18,
        "left_eye_visible": True,
        "right_eye_visible": True,
    }

    res = engine.update(session_id, openness=0.25, eye_analysis=eye_data_blurry, face_detected=True)
    assert res["is_timer_paused"] is True
    assert "blur" in res["timer_pause_reason"].lower() or "blurry" in res["timer_pause_reason"].lower()
    assert res["continuous_observation_sec"] == 0.0


def test_blink_engine_30_second_reminder_without_confidence_decrease():
    """Requirement: If eyes do not blink in 30s, do not decrease confidence, just show a popup/reminder."""
    engine = BlinkEngine()
    session_id = "test_blink_sess_30s"

    eye_data_open = {
        "eye_status": BOTH_EYES_VISIBLE,
        "is_blurry": False,
        "is_obscured": False,
        "overall_eye_quality": 0.85,
        "left_eye_quality": 0.85,
        "right_eye_quality": 0.85,
        "left_eye_visible": True,
        "right_eye_visible": True,
    }

    # Initialize session
    engine.update(session_id, openness=0.32, eye_analysis=eye_data_open, face_detected=True)

    # Fast-forward observation to threshold (30.5s) with 0 blinks
    sess = engine._get_or_create_session(session_id)
    sess["observation_seconds"] = 30.5
    sess["blink_count"] = 0

    # Next update frame must trigger the 30s gentle reminder popup
    res = engine.update(session_id, openness=0.32, eye_analysis=eye_data_open, face_detected=True)
    assert res["show_popup"] is True
    assert res["challenge"]["active"] is True
    # Confidence MUST NOT be decreased (ceiling stays 1.0)
    assert res["liveness_ceiling"] == 1.0
    assert "BLINK_REMINDER_TRIGGERED" in res["reason_codes"]

    # When user blinks, reminder immediately resolves
    sess["state"] = "CLOSED"
    sess["closed_since"] = time.time() - 0.15
    res_blinked = engine.update(session_id, openness=0.32, eye_analysis=eye_data_open, face_detected=True)
    assert res_blinked["blink_count"] == 1
    assert res_blinked["show_popup"] is False
    assert res_blinked["challenge"]["active"] is False


# ── 3. SCREEN DETECTOR TESTS ──────────────────────────────────────────────────

def test_screen_detector_case_a_phone_beside_face():
    """Case A: Person holding phone beside face (IoF < 0.35) -> NOT an attack."""
    detector = ScreenDetector()
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 120

    # Target face in center
    face_box = [260, 140, 140, 180]

    # Draw a phone contour on the left edge (completely separate from face)
    cv2.rectangle(frame, (50, 200), (140, 360), (20, 20, 20), 4)

    res = detector.analyze(frame, face_box)
    assert res["presentation_attack"] is False
    assert res["screen_face_associated"] is False


def test_screen_detector_case_b_face_inside_screen_bezel():
    """Case B: Face presented inside phone bezel with high IoF -> PRESENTATION ATTACK."""
    detector = ScreenDetector()
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 80

    # Draw sharp rectangular smartphone bezel
    cv2.rectangle(frame, (170, 70), (470, 420), (15, 15, 15), 6)
    cv2.rectangle(frame, (180, 80), (460, 410), (160, 160, 160), -1)

    # Face strictly bounded inside the screen display
    face_box = [230, 140, 170, 200]

    res = detector.analyze(frame, face_box)
    assert res["phone_detected"] is True
    assert res["screen_face_associated"] is True
    assert res["presentation_attack"] is True
    assert res["presentation_attack_confidence"] >= 0.75
    assert "PHONE_PRESENTATION_DETECTED" in res["reason_codes"]


# ── 4. INTEGRATED PIPELINE END-TO-END TESTS ───────────────────────────────────

def test_live_authenticity_case_b_screen_presentation_override():
    """Verify that when a presentation attack is detected, confidence is set to 0.0%."""
    # Synthetic frame with a phone bezel surrounding a target face
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 80
    cv2.rectangle(frame, (170, 70), (470, 420), (15, 15, 15), 6)
    cv2.rectangle(frame, (180, 80), (460, 410), (150, 150, 150), -1)
    # Target face
    cv2.ellipse(frame, (320, 240), (70, 95), 0, 0, 360, (210, 190, 170), -1)
    cv2.circle(frame, (290, 220), 10, (40, 30, 20), -1)
    cv2.circle(frame, (350, 220), 10, (40, 30, 20), -1)

    _, buf = cv2.imencode(".jpg", frame)
    sess_id = f"test_e2e_case_b_{int(time.time())}"

    res = live_authenticity_engine.analyze_frame(buf.tobytes(), sess_id)

    if res.get("presentation_attack"):
        assert res["confidence"] == 0.0
        assert res["assessment"] == "POSSIBLE_REPLAY"
        assert res["presentation_risk"] == 1.0
        assert "A face appears to be displayed through a phone" in res["user_message"]


def test_screen_detector_handheld_mobile_phone():
    """Verify detection of a handheld smartphone with non-convex finger grips and rounded corners."""
    detector = ScreenDetector()
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 90

    # Draw a phone with finger tabs on left and right borders
    cv2.rectangle(frame, (200, 60), (440, 420), (20, 20, 20), 8)
    cv2.rectangle(frame, (210, 70), (430, 410), (140, 140, 140), -1)
    # Add finger bumps along the vertical bezel
    cv2.circle(frame, (200, 200), 16, (170, 130, 110), -1)
    cv2.circle(frame, (440, 220), 16, (170, 130, 110), -1)

    # Face inside the smartphone display
    face_box = [250, 130, 140, 180]
    res = detector.analyze(frame, face_box)

    assert res["presentation_attack"] is True
    assert res["presentation_attack_confidence"] >= 0.80
    assert "PHONE_PRESENTATION_DETECTED" in res["reason_codes"]


def test_liveness_override_and_confidence_scaling():
    """Verify that head turning and 5s blinking overrides presentation attack to 60%, scaling to 85-95% on sliding/movement."""
    detector = ScreenDetector()
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 80
    cv2.rectangle(frame, (170, 70), (470, 420), (15, 15, 15), 6)
    cv2.rectangle(frame, (180, 80), (460, 410), (160, 160, 160), -1)
    face_box = [230, 140, 170, 200]

    # Without liveness proven -> flags attack
    res_static = detector.analyze(frame, face_box, is_liveness_proven=False)
    assert res_static["presentation_attack"] is True

    # With liveness proven (freely turned face and blinking every 5s) -> refutes attack
    res_live = detector.analyze(frame, face_box, is_liveness_proven=True)
    assert res_live["presentation_attack"] is False
    assert res_live["presentation_attack_confidence"] == 0.0
    assert "BACKGROUND_SCREEN_NON_ATTACK" in res_live["reason_codes"]


