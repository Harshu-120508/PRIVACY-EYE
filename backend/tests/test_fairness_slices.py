"""
Privacy Eye — Phase 4 Fairness Slices Unit Tests.

SYNTHETIC PROXY - NOT ACCURACY.
These test fixtures are synthetic mock data allowed ONLY for verifying the
statistical computation logic of slice BPCER, Wilson score confidence intervals,
and material degradation detection.
NEVER used to claim production accuracy or empirical performance.
"""
import sys
import tempfile
import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.eval_fairness_slices import (
    wilson,
    compute_slice_metrics,
    parse_slice_from_filename,
    run_fairness_evaluation,
    SLICES,
)


def test_wilson_confidence_intervals():
    """Verify Wilson score confidence interval computation."""
    # 0 errors out of 10
    lo, hi = wilson(0, 10)
    assert 0.0 <= lo < 0.01
    assert 0.25 < hi < 0.32

    # 5 errors out of 10
    lo5, hi5 = wilson(5, 10)
    assert 0.20 < lo5 < 0.28
    assert 0.72 < hi5 < 0.80

    # 0 out of 0
    lo0, hi0 = wilson(0, 0)
    assert lo0 != lo0  # NaN check


def test_filename_slice_tag_parser():
    """Verify filename-based slice attribute extraction."""
    fname = "subj01_skintone-dark_light-dim_glasses-yes_cam-720p_bg-office.mp4"
    tags = parse_slice_from_filename(fname)
    assert tags.get("skin_tone") == "dark"
    assert tags.get("lighting") == "dim"
    assert tags.get("glasses") == "yes"
    assert tags.get("camera") == "720p"
    assert tags.get("background") == "office"


def test_slice_bpcer_and_disparity_flagging():
    """
    SYNTHETIC PROXY - NOT ACCURACY.
    Verify that compute_slice_metrics correctly flags slices that perform
    materially worse than the overall average BPCER.
    """
    overall_bpcer = 0.05  # 5% average reject rate

    # Create mock clips:
    # Group A: 10 clips, 0 rejected -> BPCER = 0.0% (normal)
    # Group B: 10 clips, 4 rejected -> BPCER = 40.0% (materially worse: >= 1.5x and >= +10%)
    clips = []
    for i in range(10):
        clips.append({"skin_tone": "type_1", "accepted_strict": True})
    for i in range(10):
        # 4 rejected, 6 accepted
        clips.append({"skin_tone": "type_6", "accepted_strict": (i >= 4)})

    metrics = compute_slice_metrics(clips, "skin_tone", overall_bpcer, min_samples=3)
    assert len(metrics) == 2

    m_type1 = next(m for m in metrics if m["slice_value"] == "type_1")
    assert m_type1["bpcer"] == 0.0
    assert m_type1["is_materially_worse"] is False

    m_type6 = next(m for m in metrics if m["slice_value"] == "type_6")
    assert m_type6["bpcer"] == 0.40
    assert m_type6["is_materially_worse"] is True
    assert ">= 1.5x overall average" in m_type6["disparity_reason"]


def test_full_fairness_evaluation_pipeline():
    """
    SYNTHETIC PROXY - NOT ACCURACY.
    Verify end-to-end fairness summary generation and file export.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        clips_file = tmp_path / "clips.csv"
        meta_file = tmp_path / "metadata.csv"
        out_dir = tmp_path / "out"

        # Create synthetic clips.csv
        with open(clips_file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["label", "clip", "accepted_strict", "final_assessment"])
            for i in range(20):
                w.writerow(["real", f"clip_{i:02d}.mp4", True, "REAL_HUMAN_FACE"])
            for i in range(5):
                w.writerow(["attack_screen", f"attack_{i:02d}.mp4", False, "POSSIBLE_REPLAY"])

        # Create synthetic metadata.csv
        with open(meta_file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["clip", "skin_tone", "lighting", "glasses", "headwear", "camera", "background"])
            for i in range(20):
                st = "Fitzpatrick_IV" if i % 2 == 0 else "Fitzpatrick_II"
                lt = "daylight" if i < 10 else "low_light"
                gl = "yes" if i % 3 == 0 else "no"
                hw = "hat" if i % 5 == 0 else "none"
                cam = "logitech_1080p" if i % 2 == 0 else "laptop_720p"
                bg = "plain_wall" if i < 10 else "office"
                w.writerow([f"clip_{i:02d}.mp4", st, lt, gl, hw, cam, bg])

        res = run_fairness_evaluation(clips_file, meta_file, out_dir=out_dir)

        assert res["total_real"] == 20
        assert res["overall_bpcer"] == 0.0
        assert len(res["flagged_disparities"]) == 0
        assert (out_dir / "fairness_summary.txt").exists()
        assert (out_dir / "fairness_slices.csv").exists()
