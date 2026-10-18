"""
Privacy Eye — Advanced Blink State Machine, Timer, & 30-Second Notification Engine
Enforces biological blink validation, high-sensitivity temporal valley detection,
and gentle notification without artificial confidence reduction.
"""
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

MIN_BLINK_DURATION = 0.04   # 40ms minimum duration for camera frame-rate tolerance
MAX_BLINK_DURATION = 1.00   # 1000ms maximum duration (allows relaxed blinks)
BLINK_REFRACTORY_PERIOD = 0.22  # 220ms refractory period between consecutive blinks
OBSERVATION_CHALLENGE_THRESHOLD = 30.0  # 30 seconds notification threshold per user specification


class BlinkEngine:
    """
    Session-aware temporal blink tracker.
    Tracks eye closure and openness differentials with high sensitivity.
    Does NOT penalize confidence when user blinks are spaced out.
    """

    def __init__(self):
        # session_id -> session state dictionary
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "created_at": now,
                "last_frame_time": now,
                "observation_seconds": 0.0,
                "is_paused": False,
                "pause_reason": None,
                "blink_count": 0,
                "last_blink_timestamp": None,
                "blink_history": [],
                "openness_history": [],  # (timestamp, openness)
                # State machine
                "state": "OPEN",  # OPEN, CLOSED
                "closed_since": 0.0,
                # 30-second reminder state
                "challenge_active": False,
                "challenge_status": None,  # None, "REMINDER", "PASSED"
                "liveness_ceiling": 1.0,   # Always 1.0 (no confidence penalty)
            }
        return self._sessions[session_id]

    def reset_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def update(
        self,
        session_id: str,
        openness: float,
        eye_analysis: Dict[str, Any],
        face_detected: bool,
    ) -> Dict[str, Any]:
        """
        Updates blink temporal state with incoming frame.
        """
        now = time.time()
        sess = self._get_or_create_session(session_id)
        dt = max(0.001, min(0.5, now - sess["last_frame_time"]))
        sess["last_frame_time"] = now

        reason_codes = []
        user_guidance = []
        just_blinked = False

        # ── 1. Observation Qualification Check ──────────────────────────────
        # Observation timer advances when face is present and eyes are not obscured/severely blurry
        is_obscured = eye_analysis.get("is_obscured", False)
        is_blurry = eye_analysis.get("is_blurry", False)
        eye_status = eye_analysis.get("eye_status", "")
        eye_quality = eye_analysis.get("overall_eye_quality", 0.5)

        is_severely_blurry = is_blurry and (eye_status in ("EYE_TOO_BLURRY", "BOTH_EYES_NOT_VISIBLE") or eye_quality < 0.20)

        if not face_detected:
            sess["is_paused"] = True
            sess["pause_reason"] = "FACE_NOT_IN_FRAME"
        elif is_obscured:
            sess["is_paused"] = True
            sess["pause_reason"] = "EYES_OBSCURED"
        elif is_severely_blurry:
            sess["is_paused"] = True
            sess["pause_reason"] = "EYES_TOO_BLURRY"
        else:
            sess["is_paused"] = False
            sess["pause_reason"] = None
            sess["observation_seconds"] += dt

        # Blink state machine tracks as long as face is in frame and eyes aren't obscured by dark lenses
        can_observe_eyes = face_detected and not is_obscured

        # ── 2. Adaptive Openness Thresholds ─────────────────────────────────
        sess["openness_history"].append((now, openness))
        # Keep 15 seconds history
        sess["openness_history"] = [pt for pt in sess["openness_history"] if now - pt[0] <= 15.0]

        if len(sess["openness_history"]) >= 4:
            vals = [v for _, v in sess["openness_history"]]
            baseline = float(np.percentile(vals, 75))
        else:
            baseline = openness if openness > 0 else 18.0

        if baseline <= 1.0:
            threshold_close = max(0.08, baseline * 0.74)
            threshold_open = max(0.12, baseline * 0.84)
        else:
            threshold_close = max(3.5, baseline * 0.74)
            threshold_open = max(5.0, baseline * 0.84)

        # ── 3. Biological Blink State Machine & Valley Detection ────────────
        if can_observe_eyes:
            # Check A: Standard State Machine
            if sess["state"] == "OPEN":
                if openness < threshold_close:
                    sess["state"] = "CLOSED"
                    sess["closed_since"] = now
            elif sess["state"] == "CLOSED":
                if openness >= threshold_open:
                    duration = now - sess["closed_since"]
                    if MIN_BLINK_DURATION <= duration <= MAX_BLINK_DURATION:
                        if (
                            sess["last_blink_timestamp"] is None
                            or (now - sess["last_blink_timestamp"]) >= BLINK_REFRACTORY_PERIOD
                        ):
                            sess["blink_count"] += 1
                            sess["last_blink_timestamp"] = now
                            sess["blink_history"].append(now)
                            just_blinked = True
                            reason_codes.append("BLINK_DETECTED")
                            sess["challenge_active"] = False
                            sess["challenge_status"] = "PASSED"
                    sess["state"] = "OPEN"
                elif (now - sess["closed_since"]) > 1.2:
                    # Prolonged closure / looked down for > 1.2s -> reset
                    sess["state"] = "OPEN"

            # Check B: High-Sensitivity Single-Frame V-Valley Detector
            # Catches rapid blinks that occurred within a single sample interval
            if not just_blinked and len(sess["openness_history"]) >= 3:
                p_prev = sess["openness_history"][-3][1]
                p_mid = sess["openness_history"][-2][1]
                p_curr = sess["openness_history"][-1][1]

                is_dip = (p_mid < threshold_close or p_mid <= p_prev * 0.76)
                is_recovery = (p_curr >= threshold_open or p_curr >= p_mid * 1.20)

                if is_dip and is_recovery:
                    if (
                        sess["last_blink_timestamp"] is None
                        or (now - sess["last_blink_timestamp"]) >= BLINK_REFRACTORY_PERIOD
                    ):
                        sess["blink_count"] += 1
                        sess["last_blink_timestamp"] = now
                        sess["blink_history"].append(now)
                        just_blinked = True
                        reason_codes.append("BLINK_DETECTED")
                        sess["challenge_active"] = False
                        sess["challenge_status"] = "PASSED"
                        sess["state"] = "OPEN"

        # ── 4. 30-Second No-Blink Reminder Protocol ────────────────────────
        # Requirement: If no blink in 30s, DO NOT decrease confidence; just show a popup/banner.
        seconds_since_last_blink = (
            (now - sess["last_blink_timestamp"])
            if sess["last_blink_timestamp"] is not None
            else sess["observation_seconds"]
        )

        show_popup = False
        if seconds_since_last_blink >= OBSERVATION_CHALLENGE_THRESHOLD:
            show_popup = True
            reason_codes.append("BLINK_REMINDER_TRIGGERED")
            user_guidance.append("Please blink naturally to verify active presence.")
            sess["challenge_active"] = True
            sess["challenge_status"] = "REMINDER"
        else:
            if sess["challenge_active"] and just_blinked:
                sess["challenge_active"] = False
                sess["challenge_status"] = "PASSED"
                sess["observation_seconds"] = 0.0

        # Confidence is NEVER decreased; ceiling stays 1.0 always
        sess["liveness_ceiling"] = 1.0

        # Rate evaluation in rolling 10 seconds
        recent_blinks = [t for t in sess["blink_history"] if now - t <= 10.0]
        blinks_10s = len(recent_blinks)

        return {
            "blink_count": int(sess["blink_count"]),
            "last_blink_timestamp": sess["last_blink_timestamp"],
            "seconds_since_last_blink": round(float(seconds_since_last_blink), 1),
            "continuous_observation_sec": round(float(sess["observation_seconds"]), 1),
            "is_timer_paused": bool(sess["is_paused"]),
            "timer_pause_reason": sess["pause_reason"],
            "just_blinked": bool(just_blinked),
            "blinks_in_last_10s": int(blinks_10s),
            "show_popup": bool(show_popup),
            "challenge": {
                "active": bool(show_popup),
                "status": "REMINDER" if show_popup else ("PASSED" if sess["blink_count"] > 0 else None),
                "countdown": None,
                "label": "PLEASE BLINK" if show_popup else None,
                "prompt": (
                    "No blink detected in 30 seconds. Please blink naturally to verify continuous presence."
                    if show_popup
                    else None
                ),
            },
            "liveness_ceiling": 1.0,
            "reason_codes": reason_codes,
            "user_guidance": user_guidance,
        }


# Global singleton instance
blink_engine = BlinkEngine()
