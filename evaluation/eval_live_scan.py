#!/usr/bin/env python3
"""
eval_live_scan.py - measure Privacy Eye live-scan accuracy on YOUR labelled recordings.

READ-ONLY: imports your LiveAuthenticityEngine and runs it. It modifies nothing in your project.

Dataset layout (folder name = label; "real" is the only bona-fide label, every other folder is an attack):

    dataset/
      real/              genuine people on a live camera (videos or stills)
      attack_screen/     face shown on a phone / tablet / monitor
      attack_print/      printed photo
      attack_faceswap/   live face-swap (e.g. Deep-Live-Cam via virtual camera, CONSENTING people only)
      attack_ai/         AI-generated face video

Usage (PowerShell or bash), from anywhere:

    python eval_live_scan.py --backend C:\\path\\PRIVACY-EYE-main\\backend ^
        --data C:\\path\\dataset --yunet C:\\path\\face_detection_yunet.onnx --out results

What it reproduces from your real pipeline: frames resized to 640x480, JPEG quality 0.85, sampled at
~4.5 FPS (your frontend sends one frame every 220 ms). Your blink/timing code reads the wall clock, so this
script swaps in a VIRTUAL CLOCK driven by the video timestamps; recorded clips are therefore evaluated
faithfully instead of being distorted by processing speed.

Outputs: results/frames.csv, results/clips.csv, results/summary.txt
"""
import argparse
import csv
import math
import sys
import types
from pathlib import Path

import numpy as np
import cv2

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VID_EXT = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
STRICT_ACCEPT = {"REAL_HUMAN_FACE"}
LENIENT_ACCEPT = {"REAL_HUMAN_FACE", "LIKELY_HUMAN_FACE"}


def is_flagged(assessment: str) -> bool:
    """True when the engine labels the subject an attack/fake (also matches states you add later)."""
    a = (assessment or "").upper()
    return a == "POSSIBLE_REPLAY" or any(k in a for k in ("SWAP", "ATTACK", "SYNTH", "FAKE", "MANIPUL", "SPOOF"))


class VirtualClock:
    """Drop-in for the `time` module attributes the engine uses; advanced by the video's own timestamps."""

    def __init__(self):
        self.t = 1_700_000_000.0

    def time(self):
        return self.t

    def monotonic(self):
        return self.t

    def sleep(self, s):
        self.t += s


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def auroc(neg, pos):
    """P(pos > neg) + 0.5 P(tie). 0.5 = the signal cannot separate real from attack."""
    neg = np.sort(np.asarray(neg, dtype=float))
    pos = np.asarray(pos, dtype=float)
    if len(neg) == 0 or len(pos) == 0:
        return float("nan")
    lo = np.searchsorted(neg, pos, side="left")
    hi = np.searchsorted(neg, pos, side="right")
    return float((lo + 0.5 * (hi - lo)).sum() / (len(neg) * len(pos)))


def frames_from(path: Path, fps: float, max_sec: float):
    if path.suffix.lower() in IMG_EXT:
        img = cv2.imread(str(path))
        if img is not None:
            yield 0.0, img
        return
    cap = cv2.VideoCapture(str(path))
    vfps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(vfps / fps)))
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        t = i / vfps
        if t > max_sec:
            break
        if i % step == 0:
            yield t, fr
        i += 1
    cap.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, help="path to PRIVACY-EYE/backend")
    ap.add_argument("--data", required=True, help="dataset root (see docstring)")
    ap.add_argument("--yunet", default=None, help="path to face_detection_yunet.onnx (recommended)")
    ap.add_argument("--out", default="eval_results")
    ap.add_argument("--fps", type=float, default=4.5, help="frames/sec sent by the frontend (default 4.5)")
    ap.add_argument("--max-sec", type=float, default=40.0)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(args.backend).resolve()))
    try:
        import structlog  # noqa: F401
    except ImportError:  # minimal logging stand-in so the ML modules import
        st = types.ModuleType("structlog")

        class _L:
            def __getattr__(self, _):
                return lambda *a, **k: None

        st.get_logger = lambda *a, **k: _L()
        sys.modules["structlog"] = st

    import os
    os.chdir(Path(args.backend).resolve())
    import app.ml.live_authenticity as la
    import app.ml.blink_engine as be

    clock = VirtualClock()
    la.time = clock
    be.time = clock

    engine = la.LiveAuthenticityEngine(model_path=args.yunet) if args.yunet else la.LiveAuthenticityEngine()
    if engine._detector is None:
        print("WARNING: YuNet did not load - falling back to Haar cascade. Results will NOT represent production.")

    data = Path(args.data)
    labels = sorted([d.name for d in data.iterdir() if d.is_dir()])
    if "real" not in labels:
        sys.exit("dataset must contain a 'real' folder")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    frame_rows, clip_rows = [], []
    for label in labels:
        files = sorted(p for p in (data / label).rglob("*") if p.suffix.lower() in IMG_EXT | VID_EXT)
        for fi, path in enumerate(files):
            sid = f"{label}:{path.name}:{fi}"
            clock.t += 1000.0  # separate clips in time
            t_start = clock.t
            last, ever_flag, first_accept, n = None, False, None, 0
            codes = {}
            for t, fr in frames_from(path, args.fps, args.max_sec):
                clock.t = t_start + t
                fr = cv2.resize(fr, (640, 480), interpolation=cv2.INTER_AREA)
                ok, buf = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 85])  # = canvas.toDataURL(.., 0.85)
                b = buf.tobytes()
                r = engine.analyze_frame(img_bytes=b, session_id=sid, run_challenge=False)
                n += 1
                a = r.get("assessment", "")
                row = {
                    "label": label, "clip": path.name, "t": round(t, 2), "assessment": a,
                    "confidence": r.get("confidence"), "live_human_score": r.get("live_human_score"),
                    "replay_score": r.get("replay_score"), "synthetic_score": r.get("synthetic_score"),
                    "presentation_attack_score": r.get("presentation_attack_score"),
                    "blink_count": r.get("blink_count"),
                }
                if r.get("face_detected"):
                    dec = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
                    fd = engine.detect_face(dec)
                    if fd:
                        x, y, w, h = fd["box"]
                        rp = engine.detect_screen_replay(dec[y:y + h, x:x + w], dec, fd["box"])
                        sw = engine.detect_face_swap_artifacts(dec, fd["box"])
                        bz = engine._screen_detector.scan_face_perimeter_bezel(dec, fd["box"])
                        row.update({
                            "sig_moire_ratio": rp.get("moire_ratio"),
                            "sig_peak_to_median": rp.get("peak_to_median_ratio"),
                            "sig_bezel_vertical_lines": bz.get("vertical_lines"),
                            "sig_ela_std": sw.get("ela_residual_std"),
                            "sig_edge_energy": sw.get("edge_energy"),
                            "sig_face_swap_score": sw.get("face_swap_score"),
                            "sig_screen_attack_conf": r.get("presentation_attack_confidence"),
                            "sig_phone_conf": r.get("phone_object_confidence"),
                        })
                        bm = r.get("benchmarks", {})
                        row["sig_faceforensics"] = bm.get("faceforensics", {}).get("score")
                        row["sig_celeb_df"] = bm.get("celeb_df", {}).get("score")
                        row["sig_silent_face"] = bm.get("silent_face", {}).get("score")
                for c in r.get("reason_codes", []) or []:
                    codes[c] = codes.get(c, 0) + 1
                frame_rows.append(row)
                last = a
                ever_flag = ever_flag or is_flagged(a)
                if first_accept is None and a in STRICT_ACCEPT:
                    first_accept = round(t, 2)
            clip_rows.append({
                "label": label, "clip": path.name, "frames": n, "final_assessment": last,
                "ever_flagged": ever_flag, "final_flagged": is_flagged(last or ""),
                "accepted_strict": last in STRICT_ACCEPT, "accepted_lenient": last in LENIENT_ACCEPT,
                "first_strict_accept_sec": first_accept,
                "top_reason_codes": ";".join(sorted(codes, key=codes.get, reverse=True)[:3]),
            })
            print(f"[{label}] {path.name:40} frames={n:3} final={last}")

    # ---- write CSVs
    def dump(rows, name):
        if not rows:
            return
        keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in rows[0], k))
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    dump(frame_rows, "frames.csv")
    dump(clip_rows, "clips.csv")

    # ---- summary
    L = []
    real = [c for c in clip_rows if c["label"] == "real"]
    L.append(f"REAL clips: {len(real)} | attack types: {[l for l in labels if l != 'real']}")
    if len(real) < 30:
        L.append("NOTE: fewer than ~30 distinct real subjects -> estimates are rough; use the 95% intervals shown.")
    L.append("\n== BONA FIDE (real people) ==")

    def rate(rows, key):
        k = sum(1 for r in rows if r[key])
        n = len(rows)
        lo, hi = wilson(k, n)
        return k, n, (k / n if n else float('nan')), lo, hi

    for key, name in (("final_flagged", "falsely flagged as attack/AI at end of clip"),
                      ("ever_flagged", "flagged as attack/AI at ANY frame"),
                      ("accepted_strict", "accepted as REAL_HUMAN_FACE at end"),
                      ("accepted_lenient", "accepted as REAL/LIKELY human at end")):
        k, n, p, lo, hi = rate(real, key)
        L.append(f"  {name:48} {k}/{n} = {p:6.1%}  (95% CI {lo:.1%}-{hi:.1%})")
    k, n, p, lo, hi = rate(real, "accepted_strict")
    bpcer = 1 - p if n else float("nan")
    L.append(f"  BPCER (strict) = {bpcer:.1%}")
    apcers = []
    for lab in [l for l in labels if l != "real"]:
        rows = [c for c in clip_rows if c["label"] == lab]
        k, n, p, lo, hi = rate(rows, "accepted_strict")
        k2, _, p2, lo2, hi2 = rate(rows, "accepted_lenient")
        kd, _, pd_, lod, hid = rate(rows, "final_flagged")
        apcers.append(p)
        L.append(f"\n== ATTACK: {lab} (n={n}) ==")
        L.append(f"  APCER strict  (attack accepted as REAL_HUMAN_FACE)   {k}/{n} = {p:.1%}  (95% CI {lo:.1%}-{hi:.1%})")
        L.append(f"  APCER lenient (accepted as REAL/LIKELY human)        {k2}/{n} = {p2:.1%}  (95% CI {lo2:.1%}-{hi2:.1%})")
        L.append(f"  flagged as attack at end                             {kd}/{n} = {pd_:.1%}")
    if apcers and real:
        L.append(f"\nACER (strict) = (worst APCER {max(apcers):.1%} + BPCER {bpcer:.1%}) / 2 = {(max(apcers) + bpcer) / 2:.1%}")

    L.append("\n== PER-SIGNAL DISCRIMINATION (frame level, real vs ALL attacks; 0.50 = useless, 1.0 = perfect either direction) ==")
    sigs = sorted({k for r in frame_rows for k in r if k.startswith("sig_")})
    for s in sigs:
        neg = [r[s] for r in frame_rows if r["label"] == "real" and r.get(s) is not None]
        pos = [r[s] for r in frame_rows if r["label"] != "real" and r.get(s) is not None]
        if len(neg) < 5 or len(pos) < 5:
            L.append(f"  {s:28} not enough frames")
            continue
        a = auroc(neg, pos)
        L.append(f"  {s:28} AUROC={a:.3f}  ({'higher in attacks' if a >= 0.5 else 'LOWER in attacks'})  real_median={np.median(neg):.3g}  attack_median={np.median(pos):.3g}")
    text = "\n".join(L)
    (out / "summary.txt").write_text(text, encoding="utf-8")
    print("\n" + text)
    print(f"\nWrote {out/'frames.csv'}, {out/'clips.csv'}, {out/'summary.txt'}")


if __name__ == "__main__":
    main()
