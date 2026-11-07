"""
FaceForensics++ Dataset Adapter for Privacy Eye live-scan evaluation.
Maps FaceForensics++ originals and manipulated sequences into evaluation/eval_live_scan.py layout:
  real/ -> original_sequences/youtube/ (Bona fide original videos)
  attack_faceswap/ -> manipulated_sequences/{Deepfakes, FaceSwap, Face2Face, NeuralTextures}

Preserves official train/val/test splits using official split JSON files.
Does NOT modify or copy original raw data.
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
    try:
        os.link(src, dst)
    except OSError:
        import shutil
        shutil.copyfile(src, dst)


def adapt_faceforensics(
    src_dir: Path,
    out_dir: Path,
    compression: str = "c23",
    split: str = "test",
    max_samples: int = None,
):
    src_dir = Path(src_dir).resolve()
    out_dir = Path(out_dir).resolve()

    real_out = out_dir / "real"
    fake_out = out_dir / "attack_faceswap"
    real_out.mkdir(parents=True, exist_ok=True)
    fake_out.mkdir(parents=True, exist_ok=True)

    # Load split filter if available
    split_ids = set()
    split_file = src_dir / f"{split}.json"
    if not split_file.exists():
        # Look for splits in subfolders
        candidates = list(src_dir.rglob(f"{split}.json"))
        if candidates:
            split_file = candidates[0]

    if split_file.exists():
        with open(split_file, "r", encoding="utf-8") as f:
            pairs = json.load(f)
            for pair in pairs:
                if isinstance(pair, list):
                    split_ids.update(pair)
                else:
                    split_ids.add(str(pair))

    counts = {"real": 0, "attack_faceswap": 0}
    metadata_rows = [["clip_id", "source_dataset", "manipulation_method", "compression", "split"]]

    # 1. Originals (real)
    orig_dirs = list(src_dir.rglob(f"original_sequences/**/{compression}/videos"))
    if not orig_dirs:
        orig_dirs = list(src_dir.rglob("original_sequences/**/videos"))

    for d in orig_dirs:
        for vid in d.glob("*.mp4"):
            vid_id = vid.stem
            if split_ids and vid_id not in split_ids:
                continue
            if max_samples and sum(counts.values()) >= max_samples:
                break
            dst = real_out / vid.name
            create_link(vid, dst)
            counts["real"] += 1
            metadata_rows.append([vid.name, "FaceForensics++", "none", compression, split])

    # 2. Manipulated (face swap / deepfake)
    manip_types = ["Deepfakes", "FaceSwap", "Face2Face", "NeuralTextures", "DeepFakeDetection"]
    for m_type in manip_types:
        m_dirs = list(src_dir.rglob(f"manipulated_sequences/{m_type}/**/{compression}/videos"))
        if not m_dirs:
            m_dirs = list(src_dir.rglob(f"manipulated_sequences/{m_type}/**/videos"))

        for d in m_dirs:
            for vid in d.glob("*.mp4"):
                parts = vid.stem.split("_")
                base_id = parts[0]
                if split_ids and base_id not in split_ids:
                    continue
                if max_samples and sum(counts.values()) >= max_samples:
                    break
                dst = fake_out / f"{m_type}_{vid.name}"
                create_link(vid, dst)
                counts["attack_faceswap"] += 1
                metadata_rows.append([dst.name, "FaceForensics++", m_type, compression, split])

    with open(out_dir / "metadata.csv", "w", encoding="utf-8") as f:
        for r in metadata_rows:
            f.write(",".join(r) + "\n")

    print(f"[FaceForensics++ Adapter] Split '{split}' adapted to {out_dir}: {counts}")
    return counts


def main():
    parser = argparse.ArgumentParser(description="Adapt FaceForensics++ into eval_live_scan layout")
    parser.add_argument("--src", required=True, help="Path to FaceForensics++ root")
    parser.add_argument("--out", required=True, help="Target evaluation layout directory")
    parser.add_argument("--compression", default="c23", choices=["c23", "c40", "raw"], help="Compression level")
    parser.add_argument("--split", default="test", choices=["train", "val", "test"], help="Dataset split")
    parser.add_argument("--max-samples", type=int, default=None, help="Optional sample limit")
    args = parser.parse_args()

    adapt_faceforensics(Path(args.src), Path(args.out), compression=args.compression, split=args.split, max_samples=args.max_samples)


if __name__ == "__main__":
    main()

