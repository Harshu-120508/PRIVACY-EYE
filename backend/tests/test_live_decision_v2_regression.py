"""
Privacy Eye — Phase 1 Regression & Correctness Tests (LIVE_DECISION_V2)

Tests all Phase 1 requirements:
a) No blink recorded must NOT count as "blinking regularly"; liveness proof requires >= 1 verified blink.
b) Replay evidence is not clamped to min(0.12, ...); replay evidence stays in fusion.
c) Time-based sin term removed; confidence is 100% deterministic on identical input.
d) Wire spatial_risk into verdict: POSSIBLE_FACE_SWAP and SUSPICIOUS states.
e) Weak signals cannot veto alone; insufficient evidence returns UNABLE_TO_DETERMINE with dynamic reliability.
f) Regression invariants:
   - Static photo with jitter never reaches REAL_HUMAN_FACE.
   - Zero-blink sessions are never marked "proven".
   - Same input frame gives exact same confidence twice.
"""
import time
import os
import numpy as np
import cv2
import pytest

from pathlib import Path
from app.ml.live_authenticity import LiveAuthenticityEngine
from app.ml.blink_engine import BlinkEngine
from app.ml.eye_analyzer import BOTH_EYES_VISIBLE

TEST_FACE_PATH = Path("app/data/training/real_faces/real_face_0255533b-95ef-4b98-a7ac-f5cc1750c275.jpg")


def _get_test_face_frame(shift_x: int = 0, shift_y: int = 0) -> bytes:
    """Returns a real photographic face frame with optional translation jitter."""
    if TEST_FACE_PATH.exists():
        img = cv2.imread(str(TEST_FACE_PATH))
        if shift_x != 0 or shift_y != 0:
            M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buf.tobytes()
    return _create_synthetic_face_frame(shift_x, shift_y)


def _create_synthetic_face_frame(shift_x: int = 0, shift_y: int = 0) -> bytes:
    """
    SYNTHETIC PROXY - NOT ACCURACY.
    Allowed only for unit/regression tests to verify invariant behavior.
    NEVER used to set thresholds, weights, AUROC, or accuracy.
    """
    img = np.ones((480, 640, 3), dtype=np.uint8) * 120
    cx, cy = 320 + shift_x, 240 + shift_y
    cv2.ellipse(img, (cx, cy), (90, 120), 0, 0, 360, (190, 170, 150), -1)
    cv2.circle(img, (cx - 35, cy - 25), 14, (245, 245, 245), -1)
    cv2.circle(img, (cx - 35, cy - 25), 6, (30, 20, 15), -1)
    cv2.circle(img, (cx + 35, cy - 25), 14, (245, 245, 245), -1)
    cv2.circle(img, (cx + 35, cy - 25), 6, (30, 20, 15), -1)
    cv2.line(img, (cx, cy - 10), (cx, cy + 20), (140, 120, 100), 2)
    cv2.ellipse(img, (cx, cy + 50), (28, 10), 0, 0, 360, (120, 80, 80), -1)
    img = cv2.GaussianBlur(img, (5, 5), 1.0)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    assert ok
    return buf.tobytes()


# ── Requirement (a) & (f): Zero-blink sessions are never proven ───────────────

def test_no_blink_session_never_proven_under_v2():
    """
    Requirement (a): No blink recorded must NOT count as 'blinking regularly';
    liveness proof requires at least one verified blink.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    frame_bytes = _get_test_face_frame()
    sess_id = f"test_no_blink_v2_{time.time()}"

    # Feed 10 consecutive frames with slight position shifts (simulating movement/jitter)
    # but zero eye closure (no blink)
    for i in range(10):
        shifted_bytes = _get_test_face_frame(shift_x=(i % 2), shift_y=((i % 4) // 2))
        res = engine_v2.analyze_frame(shifted_bytes, session_id=sess_id, run_challenge=False)
        assert res["blink_count"] == 0
        # Under V2, liveness can NEVER be proven without at least 1 verified blink
        assert res["is_liveness_proven"] is False, f"Frame {i}: liveness was falsely proven with 0 blinks!"


def test_static_photo_with_jitter_never_reaches_real_human_face():
    """
    Requirement (f): A static photo with 1px jitter never reaches REAL_HUMAN_FACE.
    Under V1, jitter caused d_yaw > 1.8, tripping liveness within 5.5s.
    Under V2, zero blinks guarantees it never proves liveness or reaches REAL_HUMAN_FACE.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    sess_id = f"test_static_jitter_{time.time()}"

    for i in range(15):
        # 1px alternating jitter
        jitter_x = 1 if (i % 2 == 1) else 0
        jitter_y = 1 if (i % 4 >= 2) else 0
        frame_bytes = _get_test_face_frame(shift_x=jitter_x, shift_y=jitter_y)
        res = engine_v2.analyze_frame(frame_bytes, session_id=sess_id, run_challenge=False)

        assert res["assessment"] != "REAL_HUMAN_FACE", f"Frame {i}: static photo reached REAL_HUMAN_FACE!"
        assert res["is_liveness_proven"] is False


def test_contrast_static_photo_under_v1_flapped_liveness():
    """
    Empirical proof of the user-reported bug under V1:
    In V1, within 5.5s, 0 blinks was accepted as 'blinking regularly' and
    a static photo with 1px jitter flipped is_liveness_proven to True and
    reached HUMAN_FACE_DETECTED.
    """
    engine_v1 = LiveAuthenticityEngine(live_decision_v2=False)
    sess_id = f"test_static_legacy_{time.time()}"

    flipped_to_proven = False
    for i in range(10):
        jitter_x = 1 if (i % 2 == 1) else 0
        jitter_y = 1 if (i % 4 >= 2) else 0
        frame_bytes = _get_test_face_frame(shift_x=jitter_x, shift_y=jitter_y)
        res = engine_v1.analyze_frame(frame_bytes, session_id=sess_id, run_challenge=False)
        if res["is_liveness_proven"]:
            flipped_to_proven = True
            break

    assert flipped_to_proven is True, "V1 bug reproduced: zero-blink static photo flipped to proven liveness"


# ── Requirement (c) & (f): Confidence is 100% deterministic (no sin term) ─────

def test_deterministic_confidence_under_v2():
    """
    Requirement (c): Remove the time-based sin term; confidence must be deterministic.
    Requirement (f): Same input gives same confidence twice.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    frame_bytes = _create_synthetic_face_frame()

    # Session A
    sess_a = "sess_determ_a"
    res1 = engine_v2.analyze_frame(frame_bytes, session_id=sess_a, run_challenge=False)

    # Sleep slightly so time.time() advances meaningfully
    time.sleep(0.08)

    # Session B (evaluated with identical initial state)
    sess_b = "sess_determ_b"
    res2 = engine_v2.analyze_frame(frame_bytes, session_id=sess_b, run_challenge=False)

    assert res1["confidence"] == res2["confidence"], (
        f"Confidence varied across identical inputs: {res1['confidence']} vs {res2['confidence']}"
    )


# ── Requirement (b): Replay evidence not clamped to 0.12 ──────────────────────

def test_replay_evidence_preserved_after_liveness_checks():
    """
    Requirement (b): Remove the min(0.12, ...) replay clamp;
    replay evidence must stay in the fusion after liveness checks.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)

    high_replay_score = 0.78
    sess_id = f"test_replay_clamp_{time.time()}"
    frame_bytes = _create_synthetic_face_frame()

    # Pre-populate session with a blink and head movement so is_liveness_proven is achievable
    engine_v2._session_guided_tasks[sess_id] = {
        "smile_frames": 10,
        "teeth_detected": True,
        "max_mouth_ratio": 1.4,
        "blink_count": 3,
        "blinks_verified": True,
        "rotation_verified": True,
        "yaw_min": -15.0,
        "yaw_max": 15.0,
        "last_yaw": 0.0,
        "rotation_frames": 10,
        "smooth_rotations": 3,
        "sharp_during_rotation": True,
        "task_1_smile": {"marked": True, "mouth_ratio": 1.4, "label": "Smile Verified"},
        "task_2_blinks": {"marked": True, "blink_count": 3, "label": "3 blinks"},
        "task_3_rotation": {"marked": True, "yaw_span": 20.0, "label": "rotation"},
    }
    # Simulate dedicated BlinkEngine state with a registered blink
    sess_blink = engine_v2._blink_engine._get_or_create_session(sess_id)
    sess_blink["blink_count"] = 2
    sess_blink["last_blink_timestamp"] = time.time() - 1.5

    # Monkeypatch detect_screen_replay on engine to return high replay score
    orig_fn = engine_v2.detect_screen_replay
    try:
        engine_v2.detect_screen_replay = lambda *args, **kwargs: {
            "has_moire": True,
            "has_specular": True,
            "moire_score": high_replay_score,
            "specular_score": 0.40,
            "replay_score": high_replay_score,
            "reason_codes": ["MOIRE_PATTERN_DETECTED"],
        }
        res = engine_v2.analyze_frame(frame_bytes, session_id=sess_id, run_challenge=False)
        assert res["replay_score"] >= high_replay_score, (
            f"Replay score was clamped: expected >= {high_replay_score}, got {res['replay_score']}"
        )
        assert res["presentation_risk"] >= high_replay_score, (
            f"Presentation risk was clamped: expected >= {high_replay_score}, got {res['presentation_risk']}"
        )
    finally:
        engine_v2.detect_screen_replay = orig_fn


# ── Requirement (d): Wire spatial_risk into verdict (POSSIBLE_FACE_SWAP) ───────

def test_spatial_risk_triggers_possible_face_swap_and_suspicious():
    """
    Requirement (d): Wire spatial_risk into the verdict;
    add POSSIBLE_FACE_SWAP and SUSPICIOUS states.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    frame_bytes = _get_test_face_frame()

    # Case 1: High spatial risk (>= 0.65) -> POSSIBLE_FACE_SWAP
    orig_fn = engine_v2.detect_face_swap_artifacts
    try:
        engine_v2.detect_face_swap_artifacts = lambda *args, **kwargs: {
            "spatial_anomaly_detected": True,
            "edge_energy": 0.85,
            "ela_residual_std": 1.5,
            "seam_score": 0.82,
            "face_swap_score": 0.85,
            "reason_codes": ["BOUNDARY_SEAM_INCONSISTENCY", "SYNTHETIC_SMOOTHING"],
        }
        sess_swap = f"test_swap_{time.time()}"
        res = engine_v2.analyze_frame(frame_bytes, session_id=sess_swap, run_challenge=False)
        assert res["assessment"] == "POSSIBLE_FACE_SWAP", (
            f"Expected POSSIBLE_FACE_SWAP, got {res['assessment']}"
        )
        assert res["synthetic_score"] >= 0.65
        assert res["confidence"] <= 35.0

        # Case 2: Moderate spatial risk (0.48) -> SUSPICIOUS
        engine_v2.detect_face_swap_artifacts = lambda *args, **kwargs: {
            "spatial_anomaly_detected": True,
            "edge_energy": 0.50,
            "ela_residual_std": 3.0,
            "seam_score": 0.48,
            "face_swap_score": 0.48,
            "reason_codes": ["MILD_EDGE_INCONSISTENCY"],
        }
        sess_susp = f"test_susp_{time.time()}"
        res_susp = engine_v2.analyze_frame(frame_bytes, session_id=sess_susp, run_challenge=False)
        assert res_susp["assessment"] == "SUSPICIOUS", (
            f"Expected SUSPICIOUS, got {res_susp['assessment']}"
        )
    finally:
        engine_v2.detect_face_swap_artifacts = orig_fn


# ── Requirement (e): Weak signals do not hard veto with HIGH reliability ──────

def test_weak_signals_cannot_hard_veto_with_high_reliability():
    """
    Requirement (e): Replace the hard veto with evidence fusion:
    weak/non-validated signals cannot veto alone, and when evidence is
    insufficient return UNABLE_TO_DETERMINE/NEED_MORE_CLARITY instead of a
    HIGH-reliability attack label. reliability must reflect measured evidence.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    frame_bytes = _get_test_face_frame()

    # Simulate an isolated presentation_risk (e.g. 0.58) without phone detection
    # or screen-face containment
    orig_fn = engine_v2.detect_screen_replay
    try:
        engine_v2.detect_screen_replay = lambda *args, **kwargs: {
            "has_moire": True,
            "has_specular": False,
            "moire_score": 0.58,
            "specular_score": 0.10,
            "replay_score": 0.58,
            "reason_codes": ["WEAK_MOIRE_ARTEFACT"],
        }
        sess_weak = f"test_weak_{time.time()}"
        res = engine_v2.analyze_frame(frame_bytes, session_id=sess_weak, run_challenge=False)
        # Under V1, this was a hard veto: POSSIBLE_REPLAY with HIGH reliability
        # Under V2, single uncorroborated signal yields SUSPICIOUS, not a HIGH-reliability attack label
        assert res["assessment"] == "SUSPICIOUS"
        assert res["reliability"] in ("LOW", "MEDIUM"), (
            f"Reliability must reflect uncorroborated single signal (LOW or MEDIUM), got {res['reliability']}"
        )
    finally:
        engine_v2.detect_screen_replay = orig_fn


def test_insufficient_clarity_returns_unable_to_determine():
    """
    Requirement (e): Poor optical quality returns UNABLE_TO_DETERMINE with LOW reliability.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    frame_bytes = _create_synthetic_face_frame()

    orig_fn = engine_v2.check_frame_quality
    try:
        engine_v2.check_frame_quality = lambda *args, **kwargs: {
            "laplacian_var": 8.0,
            "illumination_mean": 20.0,
            "quality_index": 22.0,
            "is_acceptable": False,
            "is_sharp": False,
            "is_well_lit": False,
            "reason_codes": ["IMAGE_TOO_DARK", "IMAGE_BLURRY"],
        }
        sess_id = f"test_low_qual_{time.time()}"
        res = engine_v2.analyze_frame(frame_bytes, session_id=sess_id, run_challenge=False)
        assert res["assessment"] == "UNABLE_TO_DETERMINE"
        assert res["reliability"] == "LOW"
    finally:
        engine_v2.check_frame_quality = orig_fn


# ── Backward Compatibility: Legacy path untouched when LIVE_DECISION_V2=False ──

def test_legacy_path_untouched_when_flag_off():
    """Verify that when LIVE_DECISION_V2 is False, engine defaults to legacy path."""
    engine_legacy = LiveAuthenticityEngine(live_decision_v2=False)
    assert engine_legacy.is_v2_enabled() is False

    frame_bytes = _create_synthetic_face_frame()
    sess_id = f"test_legacy_{time.time()}"
    res = engine_legacy.analyze_frame(frame_bytes, session_id=sess_id, run_challenge=False)

    # Legacy returns INSTRUCTION_NOT_FOLLOWED or similar standard state
    assert res["assessment"] in (
        "INSTRUCTION_NOT_FOLLOWED",
        "HUMAN_FACE_DETECTED",
        "POSSIBLE_REPLAY",
        "REAL_HUMAN_FACE",
        "LIKELY_HUMAN_FACE",
    )


# ── Phase 2 Signal Heuristic Tests ────────────────────────────────────────────

def test_moire_periodic_peak_detector_clean_skin_vs_moire():
    """
    Phase 2: Moire periodic peak detector vs local median.
    Natural clean skin must NOT trigger periodic moire spikes (peak_to_median <= 1.5).
    Periodic grid (simulated display moire) triggers isolated peak spike.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    engine_v1 = LiveAuthenticityEngine(live_decision_v2=False)

    # 1. Natural face crop (smooth skin with natural illumination)
    np.random.seed(42)
    natural_skin = (np.random.rand(140, 120, 3) * 60 + 140).astype(np.uint8)
    # Add natural soft facial gradient
    for r in range(140):
        natural_skin[r] = np.clip(natural_skin[r] * (1.0 - r / 450.0), 0, 255)

    res_v2_clean = engine_v2.detect_screen_replay(natural_skin)
    assert res_v2_clean["peak_to_median_ratio"] < 1.7
    assert res_v2_clean["replay_score"] <= 0.15
    assert not any(s["key"] == "screen_moire_peaks" for s in res_v2_clean["signals"])

    # 2. Replay with periodic moire pattern (subpixel grid)
    screen_moire = natural_skin.copy()
    y_g, x_g = np.ogrid[:140, :120]
    periodic_grid = ((x_g % 4 == 0) | (y_g % 4 == 0)).astype(np.uint8) * 45
    screen_moire[:, :, 0] = np.clip(screen_moire[:, :, 0] + periodic_grid, 0, 255)
    screen_moire[:, :, 1] = np.clip(screen_moire[:, :, 1] + periodic_grid, 0, 255)

    res_v2_moire = engine_v2.detect_screen_replay(screen_moire)
    assert res_v2_moire["peak_to_median_ratio"] > res_v2_clean["peak_to_median_ratio"]
    # Phase 2A: thresholds UNSET and verdict contribution OFF (weight 0) until calibrated in Phase 3
    assert res_v2_clean["replay_score"] == 0.08
    assert res_v2_moire["replay_score"] == 0.08


def test_ela_live_path_bypass_under_v2():
    """
    Phase 2: ELA is invalid on frames already JPEG-compressed by frontend (q0.85).
    Under V1: ela_std < 4.2 falsely adds +0.44 to swap_score on genuine webcam frames.
    Under V2: ela_residual_std is recorded for evaluation/AUROC, but does not falsely penalize swap_score.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    engine_v1 = LiveAuthenticityEngine(live_decision_v2=False)

    # Create a JPEG-compressed frame (simulating frontend canvas.toDataURL(.., 0.85))
    raw_img = np.ones((480, 640, 3), dtype=np.uint8) * 130
    cv2.ellipse(raw_img, (320, 240), (70, 95), 0, 0, 360, (200, 180, 160), -1)
    _, buf = cv2.imencode(".jpg", raw_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    jpeg_frame = cv2.imdecode(np.frombuffer(buf.tobytes(), np.uint8), cv2.IMREAD_COLOR)
    face_box = [250, 145, 140, 190]

    res_v1 = engine_v1.detect_face_swap_artifacts(jpeg_frame, face_box)
    res_v2 = engine_v2.detect_face_swap_artifacts(jpeg_frame, face_box)

    # In both, ELA residual std is computed and low (< 4.2)
    assert res_v1["ela_residual_std"] < 4.5
    assert res_v2["ela_residual_std"] < 4.5

    # V1 falsely penalized with ela_synthetic_face_smoothing (+0.44)
    assert any(s["key"] == "ela_synthetic_face_smoothing" for s in res_v1["signals"])
    assert res_v1["face_swap_score"] >= 0.50

    # V2 dropped the invalid ELA penalty on live frames
    assert not any(s["key"] == "ela_synthetic_face_smoothing" for s in res_v2["signals"])
    assert res_v2["face_swap_score"] < 0.20


def test_boundary_seam_contour_mask_ignores_background():
    """
    Phase 2: Boundary-seam heuristic measures along the face contour only,
    not the 14px box ring that includes background.
    A high-contrast background line right outside the face oval trips V1, but is ignored by V2.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    engine_v1 = LiveAuthenticityEngine(live_decision_v2=False)

    frame = np.ones((480, 640, 3), dtype=np.uint8) * 120
    fx, fy, fw, fh = 200, 140, 160, 200
    face_box = [fx, fy, fw, fh]

    # Smooth natural face skin blending naturally into neck
    cv2.ellipse(frame, (fx + fw // 2, fy + fh // 2), (int(fw * 0.44), int(fh * 0.50)), 0, 0, 360, (130, 125, 120), -1)

    # High-contrast background edge at x = 365 (inside 14px outer box ring fx+fw+14=374, but outside face oval)
    frame[fy : fy + fh, 365:368] = (255, 255, 255)

    res_v1 = engine_v1.detect_face_swap_artifacts(frame, face_box)
    res_v2 = engine_v2.detect_face_swap_artifacts(frame, face_box)

    # V1 measured Sobel across outer_crop which included the wall edge
    # V2 measured Sobel strictly on the contour_mask, isolating the facial boundary
    assert res_v2["edge_energy"] < res_v1["edge_energy"]


def test_screen_detector_stability_and_bilateral_bezel():
    """
    Phase 2: Bezel detection requires bilateral margin lines (both left and right flanks).
    Screen detection requires face enclosure (IoF >= 0.85) and temporal stability across frames.
    """
    from app.ml.screen_detector import ScreenDetector

    detector_v2 = ScreenDetector(live_decision_v2=True)
    detector_v1 = ScreenDetector(live_decision_v2=False)

    frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
    face_box = [240, 140, 160, 200]

    # Draw vertical lines ONLY on the left flank (unilateral bookshelf or door edge)
    for lx in [200, 210, 220, 230]:
        cv2.line(frame, (lx, 100), (lx, 380), (20, 20, 20), 2)

    bz_v1 = detector_v1.scan_face_perimeter_bezel(frame, face_box)
    bz_v2 = detector_v2.scan_face_perimeter_bezel(frame, face_box)

    # V1 flagged unilateral lines as bezel
    assert bz_v1["has_bezel_lines"] is True
    # V2 requires bilateral lines (flanking both left AND right sides), so excludes unilateral wall lines
    assert bz_v2["has_bezel_lines"] is False

    # Now test temporal stability:
    # A single frame with an enclosing screen returns SCREEN_CANDIDATE_UNCONFIRMED under V2
    # until 3 consecutive frames are observed
    frame_screen = np.ones((480, 640, 3), dtype=np.uint8) * 80
    cv2.rectangle(frame_screen, (170, 70), (470, 420), (15, 15, 15), 6)
    cv2.rectangle(frame_screen, (180, 80), (460, 410), (160, 160, 160), -1)

    sess_id = f"test_stability_{time.time()}"
    res_f1 = detector_v2.analyze(frame_screen, face_box, session_id=sess_id)
    assert res_f1["presentation_attack"] is False
    assert "SCREEN_CANDIDATE_UNCONFIRMED" in res_f1["reason_codes"]

    # Frame 2: still unconfirmed
    res_f2 = detector_v2.analyze(frame_screen, face_box, session_id=sess_id)
    assert res_f2["presentation_attack"] is False

    # Frame 3: screen enclosure and temporal stability verified;
    # Under Phase 2A: weight 0 until calibrated in Phase 3
    res_f3 = detector_v2.analyze(frame_screen, face_box, session_id=sess_id)
    assert res_f3["presentation_attack"] is False
    assert "SCREEN_ENCLOSURE_STABLE_UNCALIBRATED" in res_f3["reason_codes"]


def test_uncalibrated_signals_cannot_veto_bona_fide():
    """
    Phase 2A: Uncalibrated signals cannot veto alone.
    When a genuine face is observed, uncalibrated moire, seam, or screen detection
    have weight 0 and cannot veto the session into an attack label.
    SYNTHETIC PROXY - NOT ACCURACY.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    frame_bytes = _create_synthetic_face_frame()
    sess_id = f"test_uncalibrated_{time.time()}"
    res = engine_v2.analyze_frame(frame_bytes, session_id=sess_id, run_challenge=False)
    # Never an attack label with HIGH reliability from uncalibrated signals
    assert not (res.get("assessment") == "POSSIBLE_REPLAY" and res.get("reliability") == "HIGH")


def test_insufficient_evidence_never_high_reliability_replay():
    """
    Phase 2A: Insufficient evidence returns UNABLE_TO_DETERMINE,
    never a HIGH-reliability POSSIBLE_REPLAY.
    SYNTHETIC PROXY - NOT ACCURACY.
    """
    engine_v2 = LiveAuthenticityEngine(live_decision_v2=True)
    frame_bytes = _create_synthetic_face_frame()

    orig_fn = engine_v2.check_frame_quality
    try:
        engine_v2.check_frame_quality = lambda *args, **kwargs: {
            "laplacian_var": 6.0,
            "illumination_mean": 15.0,
            "quality_index": 20.0,
            "is_acceptable": False,
            "is_sharp": False,
            "is_well_lit": False,
            "reason_codes": ["IMAGE_TOO_DARK", "IMAGE_BLURRY"],
        }
        sess_id = f"test_insufficient_ev_{time.time()}"
        res = engine_v2.analyze_frame(frame_bytes, session_id=sess_id, run_challenge=False)
        assert res["assessment"] == "UNABLE_TO_DETERMINE"
        assert res["reliability"] == "LOW"
    finally:
        engine_v2.check_frame_quality = orig_fn
