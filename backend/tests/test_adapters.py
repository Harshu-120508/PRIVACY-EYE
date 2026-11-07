"""
Unit tests for dataset adapters (DFDC, Replay-Attack, FaceForensics++).
All test fixtures in this file are tiny synthetic stubs used solely to verify
adapter parsing, link generation, and folder layout compliance.

SYNTHETIC PROXY - NOT ACCURACY.
NEVER set a threshold, weight, AUROC, APCER/BPCER or accuracy from these stubs.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure tools are importable
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.adapters.dfdc_adapter import adapt_dfdc
from tools.adapters.replay_attack_adapter import adapt_replay_attack
from tools.adapters.faceforensics_adapter import adapt_faceforensics


def test_dfdc_adapter_synthetic_stub(tmp_path):
    # SYNTHETIC PROXY - NOT ACCURACY
    src_dir = tmp_path / "dfdc_source"
    part_dir = src_dir / "dfdc_train_part_00"
    part_dir.mkdir(parents=True)

    # Create dummy video files
    (part_dir / "real_sample.mp4").write_bytes(b"dummy_mp4_bytes")
    (part_dir / "fake_sample.mp4").write_bytes(b"dummy_mp4_bytes")

    # Create official metadata.json structure
    meta = {
        "real_sample.mp4": {"label": "REAL", "split": "train"},
        "fake_sample.mp4": {"label": "FAKE", "split": "train", "original": "real_sample.mp4"},
    }
    (part_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

    out_dir = tmp_path / "dfdc_eval_layout"
    counts = adapt_dfdc(src_dir, out_dir)

    assert counts["real"] == 1
    assert counts["attack_faceswap"] == 1
    assert (out_dir / "real" / "real_sample.mp4").exists()
    assert (out_dir / "attack_faceswap" / "fake_sample.mp4").exists()
    assert (out_dir / "metadata.csv").exists()


def test_replay_attack_adapter_synthetic_stub(tmp_path):
    # SYNTHETIC PROXY - NOT ACCURACY
    src_dir = tmp_path / "replay_source"
    devel_dir = src_dir / "devel"
    (devel_dir / "real").mkdir(parents=True)
    (devel_dir / "attack" / "fixed" / "print").mkdir(parents=True)
    (devel_dir / "attack" / "hand" / "mobile").mkdir(parents=True)

    (devel_dir / "real" / "client001_session01_webcam.mov").write_bytes(b"dummy_mov")
    (devel_dir / "attack" / "fixed" / "print" / "client001_session01_print.mov").write_bytes(b"dummy_mov")
    (devel_dir / "attack" / "hand" / "mobile" / "client001_session01_mobile.mov").write_bytes(b"dummy_mov")

    out_dir = tmp_path / "replay_eval_layout"
    counts = adapt_replay_attack(src_dir, out_dir, split="devel")

    assert counts["real"] == 1
    assert counts["attack_print"] == 1
    assert counts["attack_screen"] == 1
    assert (out_dir / "real" / "client001_session01_webcam.mov").exists()
    assert (out_dir / "attack_print" / "fixed_client001_session01_print.mov").exists()
    assert (out_dir / "attack_screen" / "hand_mobile_client001_session01_mobile.mov").exists()
    assert (out_dir / "metadata.csv").exists()


def test_faceforensics_adapter_synthetic_stub(tmp_path):
    # SYNTHETIC PROXY - NOT ACCURACY
    src_dir = tmp_path / "ff_source"
    orig_vid_dir = src_dir / "original_sequences" / "youtube" / "c23" / "videos"
    orig_vid_dir.mkdir(parents=True)
    (orig_vid_dir / "001.mp4").write_bytes(b"dummy_mp4")

    deepfakes_dir = src_dir / "manipulated_sequences" / "Deepfakes" / "c23" / "videos"
    deepfakes_dir.mkdir(parents=True)
    (deepfakes_dir / "001_002.mp4").write_bytes(b"dummy_mp4")

    # Official split file
    (src_dir / "test.json").write_text(json.dumps([["001", "002"]]), encoding="utf-8")

    out_dir = tmp_path / "ff_eval_layout"
    counts = adapt_faceforensics(src_dir, out_dir, split="test")

    assert counts["real"] == 1
    assert counts["attack_faceswap"] == 1
    assert (out_dir / "real" / "001.mp4").exists()
    assert (out_dir / "attack_faceswap" / "Deepfakes_001_002.mp4").exists()
    assert (out_dir / "metadata.csv").exists()

