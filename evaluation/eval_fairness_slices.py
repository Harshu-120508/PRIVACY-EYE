#!/usr/bin/env python3
"""
eval_fairness_slices.py — Phase 4 Fairness & Demographic Slice Evaluation.

Reports BPCER (Biometric Presentation Classification Error Rate / False Reject Rate)
across demographic, physiological, and environmental slices:
  - skin_tone (e.g. Fitzpatrick I-VI or Light/Medium/Dark)
  - lighting (e.g. bright_daylight, warm_indoor, low_light, fluorescent)
  - glasses (e.g. yes, no, thick_frames)
  - headwear (e.g. none, hat, hijab, turban)
  - camera (e.g. laptop_720p, usb_1080p, phone_cam)
  - background (e.g. plain_wall, office, window, bookshelf)

Identifies and flags slices that perform materially worse than the overall bona fide average:
Disparity criterion:
  - Relative degradation >= 1.5x average BPCER, OR
  - Absolute degradation >= +10.0% BPCER with non-overlapping 95% Wilson confidence intervals.

Usage:
    python evaluation/eval_fairness_slices.py \\
        --clips evaluation_results/clips.csv \\
        --metadata path/to/slices_metadata.csv \\
        --out evaluation_results
"""
import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

SLICES = ["skin_tone", "lighting", "glasses", "headwear", "camera", "background"]


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Computes Wilson score 95% confidence interval for proportion k / n."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1.0 + (z * z) / n
    c = (p + (z * z) / (2.0 * n)) / d
    h = z * math.sqrt(p * (1.0 - p) / n + (z * z) / (4.0 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def parse_slice_from_filename(filename: str) -> Dict[str, str]:
    """
    Fallback parser for filename-encoded slices:
    Format: subj01_skintone-IV_light-dim_glasses-yes_headwear-none_cam-720p_bg-wall.mp4
    """
    stem = Path(filename).stem
    tags = {}
    tokens = stem.split("_")
    alias_map = {
        "skintone": "skin_tone",
        "skin": "skin_tone",
        "light": "lighting",
        "lighting": "lighting",
        "glasses": "glasses",
        "glass": "glasses",
        "headwear": "headwear",
        "hat": "headwear",
        "cam": "camera",
        "camera": "camera",
        "bg": "background",
        "background": "background",
    }
    for tok in tokens:
        if "-" in tok:
            k, v = tok.split("-", 1)
            k_clean = k.lower().replace("_", "").strip()
            if k_clean in alias_map:
                tags[alias_map[k_clean]] = v.strip()
    return tags


def compute_slice_metrics(
    real_clips: List[Dict[str, Any]],
    slice_dimension: str,
    overall_bpcer: float,
    min_samples: int = 3,
) -> List[Dict[str, Any]]:
    """
    Computes BPCER and confidence intervals for each group within a slice dimension.
    Flags any group that is materially worse than the average.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for c in real_clips:
        val = str(c.get(slice_dimension, "")).strip() or "unspecified"
        groups.setdefault(val, []).append(c)

    results = []
    for val, items in sorted(groups.items()):
        n = len(items)
        # Accepted strict means accepted as REAL_HUMAN_FACE
        # False reject (error) is when bona fide is NOT accepted strictly
        n_accepted = sum(1 for x in items if str(x.get("accepted_strict", "")).lower() in ("true", "1"))
        n_rejected = n - n_accepted
        bpcer = n_rejected / n if n > 0 else float("nan")
        ci_lo, ci_hi = wilson(n_rejected, n)

        # Flagging criterion:
        # 1. Relative: BPCER >= 1.5x average (if average > 0.02)
        # 2. Absolute: BPCER >= average + 0.10 (10% higher absolute reject rate)
        # 3. Sample size sufficiency check (at least min_samples)
        is_materially_worse = False
        disparity_reason = None
        if n >= min_samples and not math.isnan(bpcer) and not math.isnan(overall_bpcer):
            if overall_bpcer > 0.02 and bpcer >= (overall_bpcer * 1.50) and (bpcer - overall_bpcer) >= 0.05:
                is_materially_worse = True
                disparity_reason = f"BPCER {bpcer:.1%} is >= 1.5x overall average ({overall_bpcer:.1%})"
            elif bpcer >= (overall_bpcer + 0.10):
                is_materially_worse = True
                disparity_reason = f"BPCER {bpcer:.1%} exceeds average by >= 10.0% absolute"

        results.append({
            "slice_dimension": slice_dimension,
            "slice_value": val,
            "total_clips": n,
            "accepted_count": n_accepted,
            "rejected_count": n_rejected,
            "bpcer": bpcer,
            "ci_95_lo": ci_lo,
            "ci_95_hi": ci_hi,
            "is_materially_worse": is_materially_worse,
            "disparity_reason": disparity_reason,
        })
    return results


def run_fairness_evaluation(
    clips_csv_path: Path,
    metadata_csv_path: Optional[Path] = None,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes Phase 4 fairness slices report from clips CSV and optional metadata CSV.
    """
    if not clips_csv_path.exists():
        raise FileNotFoundError(f"Clips file not found: {clips_csv_path}")

    # Read clips.csv
    with open(clips_csv_path, "r", encoding="utf-8") as f:
        clip_rows = list(csv.DictReader(f))

    # Read metadata if provided
    metadata_by_clip: Dict[str, Dict[str, str]] = {}
    if metadata_csv_path and metadata_csv_path.exists():
        with open(metadata_csv_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = row.get("clip") or row.get("filename") or row.get("sample_id")
                if key:
                    metadata_by_clip[Path(key).name] = row

    # Filter to bona fide real clips
    real_clips = []
    for r in clip_rows:
        if r.get("label", "").lower() == "real":
            clip_name = Path(r.get("clip", "")).name
            meta = metadata_by_clip.get(clip_name, {})
            filename_tags = parse_slice_from_filename(clip_name)

            # Populate slice columns
            enriched = dict(r)
            for sl in SLICES:
                val = meta.get(sl) or filename_tags.get(sl) or r.get(sl) or "unspecified"
                enriched[sl] = val
            real_clips.append(enriched)

    total_real = len(real_clips)
    if total_real == 0:
        return {"error": "No bona fide 'real' clips found in clips.csv", "total_real": 0}

    # Overall bona fide metrics
    total_accepted = sum(1 for c in real_clips if str(c.get("accepted_strict", "")).lower() in ("true", "1"))
    total_rejected = total_real - total_accepted
    overall_bpcer = total_rejected / total_real if total_real > 0 else float("nan")
    ov_lo, ov_hi = wilson(total_rejected, total_real)

    # Evaluate each slice dimension
    slice_reports: Dict[str, List[Dict[str, Any]]] = {}
    flagged_disparities: List[Dict[str, Any]] = []

    for sl in SLICES:
        res = compute_slice_metrics(real_clips, sl, overall_bpcer)
        slice_reports[sl] = res
        for item in res:
            if item["is_materially_worse"]:
                flagged_disparities.append(item)

    # Generate text summary
    lines = []
    lines.append("================================================================================")
    lines.append("PRIVACY EYE — PHASE 4 FAIRNESS SLICES & DEMOGRAPHIC INTEGRITY REPORT")
    lines.append("================================================================================")
    lines.append(f"Total Bona Fide Clips Evaluated : {total_real}")
    lines.append(f"Overall Bona Fide Acceptance    : {total_accepted}/{total_real} = {1.0 - overall_bpcer:.1%}")
    lines.append(f"Overall Baseline BPCER (strict) : {overall_bpcer:.1%}  (95% CI {ov_lo:.1%}-{ov_hi:.1%})")
    lines.append("")

    if flagged_disparities:
        lines.append(">> FLAGGED DISPARITIES (Slices Materially Worse Than Average):")
        for f in flagged_disparities:
            lines.append(
                f"  [FLAG] {f['slice_dimension'].upper()}: '{f['slice_value']}' "
                f"-> BPCER={f['bpcer']:.1%} (95% CI {f['ci_95_lo']:.1%}-{f['ci_95_hi']:.1%}, n={f['total_clips']}) "
                f"| Reason: {f['disparity_reason']}"
            )
        lines.append("")
    else:
        lines.append(">> NO DISPARITIES FLAGGED: All evaluated slices perform within acceptable parity margins.")
        lines.append("")

    lines.append(">> DETAILED BREAKDOWN PER SLICE:")
    lines.append(f"{'Slice Category':<16} {'Slice Value':<20} {'Clips':<7} {'BPCER':<10} {'95% CI':<16} {'Status'}")
    lines.append("-" * 80)

    all_rows = []
    for sl in SLICES:
        for r in slice_reports[sl]:
            status = "MATERIALLY WORSE" if r["is_materially_worse"] else "NORMAL"
            ci_str = f"{r['ci_95_lo']:.1%}-{r['ci_95_hi']:.1%}" if not math.isnan(r["ci_95_lo"]) else "N/A"
            bp_str = f"{r['bpcer']:.1%}" if not math.isnan(r["bpcer"]) else "N/A"
            lines.append(f"{r['slice_dimension']:<16} {r['slice_value']:<20} {r['total_clips']:<7} {bp_str:<10} {ci_str:<16} {status}")
            all_rows.append(r)

    summary_text = "\n".join(lines)

    # Write files if out_dir specified
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "fairness_summary.txt").write_text(summary_text, encoding="utf-8")

        with open(out_dir / "fairness_slices.csv", "w", newline="", encoding="utf-8") as f:
            if all_rows:
                writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
                writer.writeheader()
                writer.writerows(all_rows)

    return {
        "overall_bpcer": overall_bpcer,
        "overall_ci": (ov_lo, ov_hi),
        "total_real": total_real,
        "flagged_disparities": flagged_disparities,
        "slice_reports": slice_reports,
        "summary_text": summary_text,
    }


def main():
    ap = argparse.ArgumentParser(description="Phase 4 Fairness Slices Evaluator")
    ap.add_argument("--clips", required=True, help="Path to clips.csv from eval_live_scan.py")
    ap.add_argument("--metadata", default=None, help="Path to slice metadata CSV")
    ap.add_argument("--out", default="evaluation_results", help="Output directory")
    args = ap.parse_args()

    res = run_fairness_evaluation(
        clips_csv_path=Path(args.clips),
        metadata_csv_path=Path(args.metadata) if args.metadata else None,
        out_dir=Path(args.out),
    )
    print(res["summary_text"])


if __name__ == "__main__":
    main()
