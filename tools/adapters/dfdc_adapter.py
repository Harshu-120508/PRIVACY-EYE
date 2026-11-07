"""
DFDC Dataset Adapter for Privacy Eye live-scan evaluation.
Maps Meta/Kaggle Deepfake Detection Challenge data to evaluation/eval_live_scan.py layout:
  real/ -> REAL videos
  attack_faceswap/ -> FAKE videos (Deepfake / GAN face swaps)

Does NOT modify or copy original raw data. Uses symlinks with fallback to hardlinks.
Official metadata protocol is read from metadata.json.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def create_link(src: Path, dst: Path, use_symlinks: bool = True):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if use_symlinks:
        try:
            os.symlink(src, dst)
            return
        except OSError:
            pass
    # Fallback to hardlink
    try:
        os.link(src, dst)
    except OSError:
        # Fallback to copy if cross-drive linking is disallowed
        import shutil
        shutil.copyfile(src, dst)


def adapt_dfdc(src_dir: Path, out_dir: Path, max_samples: int = None, split_filter: str = None):
    src_dir = Path(src_dir).resolve()
    out_dir = Path(out_dir).resolve()

    real_dir = out_dir / "real"
    fake_dir = out_dir / "attack_faceswap"
    real_dir.mkdir(parents=True, exist_ok=True)
    fake_dir.mkdir(parents=True, exist_ok=True)

    metadata_files = list(src_dir.rglob("metadata.json"))
    if not metadata_files:
        raise FileNotFoundError(f"No metadata.json found in {src_dir}")

    count_real = 0
    count_fake = 0

    metadata_rows = [["clip_id", "source_dataset", "ground_truth", "original_pair"]]

    for meta_p in metadata_files:
        part_dir = meta_p.parent
        with open(meta_p, "r", encoding="utf-8") as f:
            meta = json.load(f)

        for filename, info in meta.items():
            if max_samples and (count_real + count_fake) >= max_samples:
                break

            video_p = part_dir / filename
            if not video_p.exists():
                continue

            label = info.get("label", "").upper()
            split = info.get("split", "train").lower()
            if split_filter and split != split_filter.lower():
                continue

            original = info.get("original", "")

            if label == "REAL":
                target_p = real_dir / filename
                create_link(video_p, target_p)
                count_real += 1
                metadata_rows.append([filename, "DFDC", "real", ""])
            elif label == "FAKE":
                target_p = fake_dir / filename
                create_link(video_p, target_p)
                count_fake += 1
                metadata_rows.append([filename, "DFDC", "attack_faceswap", original or ""])

        if max_samples and (count_real + count_fake) >= max_samples:
            break

    # Write metadata.csv for slice evaluation
    with open(out_dir / "metadata.csv", "w", encoding="utf-8") as f:
        for r in metadata_rows:
            f.write(",".join(r) + "\n")

    print(f"[DFDC Adapter] Successfully adapted: {count_real} REAL, {count_fake} FAKE into {out_dir}")
    return {"real": count_real, "attack_faceswap": count_fake}


def main():
    parser = argparse.ArgumentParser(description="Adapt DFDC dataset into eval_live_scan layout")
    parser.add_argument("--src", required=True, help="Path to DFDC part or root directory")
    parser.add_argument("--out", required=True, help="Target evaluation layout directory")
    parser.add_argument("--max-samples", type=int, default=None, help="Optional sample limit")
    parser.add_argument("--split", default=None, help="Filter by split (e.g. train, test)")
    args = parser.parse_args()

    adapt_dfdc(Path(args.src), Path(args.out), max_samples=args.max_samples, split_filter=args.split)


if __name__ == "__main__":
    main()

