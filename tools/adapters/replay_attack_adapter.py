"""
Idiap Replay-Attack Dataset Adapter for Privacy Eye live-scan evaluation.
Maps Idiap Replay-Attack dataset into evaluation/eval_live_scan.py layout:
  real/ -> real/ videos (MacBook webcam bona fide)
  attack_print/ -> attack/*/print/ (paper print attacks)
  attack_screen/ -> attack/*/mobile/ and attack/*/highdef/ (iPhone & iPad replays)

Preserves client-disjoint train, devel, and test splits per official protocol.
Does NOT modify or copy original raw data.
"""

import argparse
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


def adapt_replay_attack(src_dir: Path, out_dir: Path, split: str = "test", max_samples: int = None):
    src_dir = Path(src_dir).resolve()
    out_dir = Path(out_dir).resolve()

    target_split_dir = src_dir / split
    if not target_split_dir.exists():
        # Fallback if src_dir is already the split directory
        if (src_dir / "real").exists():
            target_split_dir = src_dir
        else:
            raise FileNotFoundError(f"Split directory '{split}' not found under {src_dir}")

    real_out = out_dir / "real"
    print_out = out_dir / "attack_print"
    screen_out = out_dir / "attack_screen"

    for d in [real_out, print_out, screen_out]:
        d.mkdir(parents=True, exist_ok=True)

    counts = {"real": 0, "attack_print": 0, "attack_screen": 0}
    metadata_rows = [["clip_id", "source_dataset", "split", "ground_truth", "support_mode"]]

    # 1. Real videos
    real_src = target_split_dir / "real"
    if real_src.exists():
        for vid in real_src.glob("*.*"):
            if vid.suffix.lower() in [".mov", ".mp4", ".avi", ".mkv"]:
                if max_samples and sum(counts.values()) >= max_samples:
                    break
                dst = real_out / vid.name
                create_link(vid, dst)
                counts["real"] += 1
                metadata_rows.append([vid.name, "Replay-Attack", split, "real", "webcam"])

    # 2. Attack videos (fixed and hand-held)
    attack_root = target_split_dir / "attack"
    if attack_root.exists():
        for support_mode in ["fixed", "hand"]:
            mode_dir = attack_root / support_mode
            if not mode_dir.exists():
                continue

            # Print attacks
            p_dir = mode_dir / "print"
            if p_dir.exists():
                for vid in p_dir.glob("*.*"):
                    if vid.suffix.lower() in [".mov", ".mp4", ".avi", ".mkv"]:
                        if max_samples and sum(counts.values()) >= max_samples:
                            break
                        dst = print_out / f"{support_mode}_{vid.name}"
                        create_link(vid, dst)
                        counts["attack_print"] += 1
                        metadata_rows.append([dst.name, "Replay-Attack", split, "attack_print", support_mode])

            # Screen replays (mobile / highdef)
            for screen_type in ["mobile", "highdef"]:
                s_dir = mode_dir / screen_type
                if s_dir.exists():
                    for vid in s_dir.glob("*.*"):
                        if vid.suffix.lower() in [".mov", ".mp4", ".avi", ".mkv"]:
                            if max_samples and sum(counts.values()) >= max_samples:
                                break
                            dst = screen_out / f"{support_mode}_{screen_type}_{vid.name}"
                            create_link(vid, dst)
                            counts["attack_screen"] += 1
                            metadata_rows.append([dst.name, "Replay-Attack", split, "attack_screen", f"{support_mode}_{screen_type}"])

    with open(out_dir / "metadata.csv", "w", encoding="utf-8") as f:
        for r in metadata_rows:
            f.write(",".join(r) + "\n")

    print(f"[Replay-Attack Adapter] Split '{split}' adapted to {out_dir}: {counts}")
    return counts


def main():
    parser = argparse.ArgumentParser(description="Adapt Idiap Replay-Attack into eval_live_scan layout")
    parser.add_argument("--src", required=True, help="Path to Replay-Attack root")
    parser.add_argument("--out", required=True, help="Target evaluation layout directory")
    parser.add_argument("--split", default="test", choices=["train", "devel", "test"], help="Dataset split (default: test)")
    parser.add_argument("--max-samples", type=int, default=None, help="Optional sample limit")
    args = parser.parse_args()

    adapt_replay_attack(Path(args.src), Path(args.out), split=args.split, max_samples=args.max_samples)


if __name__ == "__main__":
    main()

