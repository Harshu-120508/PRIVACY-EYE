"""
Privacy Eye — Hugging Face Decoupling & Upload Pipeline
Packages and uploads models and datasets to Hugging Face Hub, decoupling them from
the web codebase so the frontend can be deployed smoothly on Vercel without large file payloads.
"""
import os
import sys
import shutil
import argparse
from pathlib import Path

try:
    from huggingface_hub import HfApi
except ImportError:
    print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
    sys.exit(1)

def prepare_model_card(username: str, models_dir: Path) -> None:
    readme_content = f"""---
language:
- en
license: mit
tags:
- deepfake-detection
- liveness-detection
- face-detection
- onnx
- computer-vision
- forensics
model-index:
- name: privacy-eye-models
  results: []
---

# Privacy Eye — ML Model Registry (v2.0)

Production model weights and provenance registry for the **Privacy Eye** multimodal deepfake & live authenticity detection system.

## Included Models & Weights

| Model Name | Pipeline | Format | File Size | SHA-256 Checksum | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `face_detection_yunet.onnx` | Live Authenticity | ONNX | 232 KB | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | OpenCV Zoo (2023mar) |
| `haarcascade_frontalface_default.xml` | Fallback Detector | XML | 933 KB | Built-in | OpenCV / Intel |
| `haarcascade_eye.xml` | Blink Fallback | XML | 341 KB | Built-in | OpenCV / Intel |

## Manifest Specification
See `manifest.json` for verified checksums, runtime requirements, and architecture parameters.

## Integration
In Privacy Eye backend, models are fetched on-demand using:
```python
from huggingface_hub import hf_hub_download
file_path = hf_hub_download(repo_id="{username}/privacy-eye-models", filename="face_detection_yunet.onnx")
```
"""
    (models_dir / "README.md").write_text(readme_content, encoding="utf-8")

def prepare_dataset_card(username: str, datasets_dir: Path) -> None:
    readme_content = f"""---
language:
- en
license: cc-by-nc-4.0
tags:
- deepfake-detection
- facial-forensics
- liveness-verification
- anti-spoofing
- evaluation-benchmark
pretty_name: Privacy Eye Benchmark & Consent Ledger
size_categories:
- n<1K
---

# Privacy Eye — Benchmark Datasets & Consent Ledger

Standardized benchmark datasets, cross-dataset evaluation manifests, and fairness slice telemetry for the **Privacy Eye** forensics platform.

## Contents
- **`manifest.csv`**: Ground-truth provenance manifest with consent status, hardware, and attack taxonomy.
- **`training/`**: Consented sample facial imagery for active calibration.
- **`eval_results_v1/` & `eval_results_v2/`**: Baseline and live-decision benchmark evaluation outputs.
- **`docs/`**: Domain gap studies, ethical licensing frameworks, and data collection protocol documentation.

## Privacy & Consent
All live biometric entries adhere strictly to the **Privacy Eye Consent Protocol (v1.0)** with explicit opt-in subject consent.
"""
    (datasets_dir / "README.md").write_text(readme_content, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Upload Privacy Eye models and datasets to Hugging Face")
    parser.add_argument("--token", type=str, default=None, help="Hugging Face Write Access Token")
    parser.add_argument("--repo-prefix", type=str, default="privacy-eye", help="Repository name prefix")
    args = parser.parse_args()

    token = args.token or os.environ.get("HF_TOKEN")
    if not token:
        print("\n" + "=" * 70)
        print("HF_TOKEN REQUIRED")
        print("=" * 70)
        print("Please provide your Hugging Face write token using one of the following:")
        print("  1. Pass --token: python tools/upload_to_huggingface.py --token hf_xxx")
        print("  2. Set env variable: $env:HF_TOKEN = 'hf_xxx'")
        print("  3. Log in with CLI: hf auth login")
        print("Get your token here: https://huggingface.co/settings/tokens (Select 'Write' role)")
        print("=" * 70 + "\n")
        sys.exit(1)

    api = HfApi(token=token)
    try:
        user_info = api.whoami()
        username = user_info["name"]
        print(f"[+] Successfully authenticated with Hugging Face as: @{username}")
    except Exception as e:
        print(f"[-] Authentication failed: {e}")
        sys.exit(1)

    repo_root = Path(__file__).resolve().parent.parent
    staging_dir = repo_root / "deploy_hf_staging"
    models_stage = staging_dir / "models"
    datasets_stage = staging_dir / "datasets"

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    models_stage.mkdir(parents=True, exist_ok=True)
    datasets_stage.mkdir(parents=True, exist_ok=True)

    print("\n[+] Staging Models...")
    # 1. Models & Weights
    if (repo_root / "models" / "manifest.json").exists():
        shutil.copy2(repo_root / "models" / "manifest.json", models_stage / "manifest.json")
    
    yunet_src = repo_root / "backend" / "app" / "ml" / "weights" / "face_detection_yunet.onnx"
    if yunet_src.exists():
        shutil.copy2(yunet_src, models_stage / "face_detection_yunet.onnx")

    eye_cascade = repo_root / "backend" / "app" / "ml" / "weights" / "haarcascade_eye.xml"
    if eye_cascade.exists():
        shutil.copy2(eye_cascade, models_stage / "haarcascade_eye.xml")

    face_cascade = repo_root / "backend" / "app" / "ml" / "weights" / "haarcascade_frontalface_default.xml"
    if face_cascade.exists():
        shutil.copy2(face_cascade, models_stage / "haarcascade_frontalface_default.xml")

    prepare_model_card(username, models_stage)
    print(f"    Staged {len(list(models_stage.iterdir()))} model artifact files.")

    print("\n[+] Staging Datasets...")
    # 2. Datasets
    if (repo_root / "datasets" / "manifest.csv").exists():
        shutil.copy2(repo_root / "datasets" / "manifest.csv", datasets_stage / "manifest.csv")

    real_faces_src = repo_root / "backend" / "app" / "data" / "training" / "real_faces"
    if real_faces_src.exists():
        shutil.copytree(real_faces_src, datasets_stage / "training" / "real_faces", dirs_exist_ok=True)

    v1_eval = repo_root / "backend" / "eval_results_user_v1"
    if v1_eval.exists():
        shutil.copytree(v1_eval, datasets_stage / "eval_results_v1", dirs_exist_ok=True)

    v2_eval = repo_root / "backend" / "eval_results_user_v2"
    if v2_eval.exists():
        shutil.copytree(v2_eval, datasets_stage / "eval_results_v2", dirs_exist_ok=True)

    docs_stage = datasets_stage / "docs"
    docs_stage.mkdir(exist_ok=True)
    for doc_name in ["dataset-domain-gap.md", "dataset-licensing.md"]:
        doc_path = repo_root / "docs" / doc_name
        if doc_path.exists():
            shutil.copy2(doc_path, docs_stage / doc_name)

    tools_dir = repo_root / "tools"
    for tool_name in ["DATASETS_VERIFIED.md", "DATA_ACCESS_PLAN.md", "DATA_COLLECTION.md"]:
        tool_path = tools_dir / tool_name
        if tool_path.exists():
            shutil.copy2(tool_path, datasets_stage / tool_name)

    prepare_dataset_card(username, datasets_stage)
    print("    Staged dataset manifests, evaluation results, and consent ledgers.")

    models_repo_id = f"{username}/{args.repo_prefix}-models"
    datasets_repo_id = f"{username}/{args.repo_prefix}-datasets"

    print(f"\n[+] Creating Hugging Face Model Repository: {models_repo_id}")
    try:
        api.create_repo(repo_id=models_repo_id, repo_type="model", exist_ok=True)
        print(f"    Repo ready: https://huggingface.co/{models_repo_id}")
    except Exception as e:
        print(f"    Notice: {e}")

    print(f"\n[+] Creating Hugging Face Dataset Repository: {datasets_repo_id}")
    try:
        api.create_repo(repo_id=datasets_repo_id, repo_type="dataset", exist_ok=True)
        print(f"    Repo ready: https://huggingface.co/datasets/{datasets_repo_id}")
    except Exception as e:
        print(f"    Notice: {e}")

    print(f"\n[+] Uploading Models to {models_repo_id}...")
    api.upload_folder(
        folder_path=str(models_stage),
        repo_id=models_repo_id,
        repo_type="model",
        commit_message="Deploy Privacy Eye ML Model weights and manifest (v2.0)"
    )
    print(f"[SUCCESS] Models uploaded: https://huggingface.co/{models_repo_id}")

    print(f"\n[+] Uploading Datasets to {datasets_repo_id}...")
    api.upload_folder(
        folder_path=str(datasets_stage),
        repo_id=datasets_repo_id,
        repo_type="dataset",
        commit_message="Deploy Privacy Eye Dataset benchmark and consent ledgers (v2.0)"
    )
    print(f"[SUCCESS] Datasets uploaded: https://huggingface.co/datasets/{datasets_repo_id}")

    # Cleanup staging directory
    shutil.rmtree(staging_dir, ignore_errors=True)

    # Automatically update backend configuration with user's repository
    manifest_path = repo_root / "models" / "manifest.json"
    if manifest_path.exists():
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        for m in manifest_data.get("models", []):
            if m.get("name") == "face_detection_yunet":
                m["repo_id"] = models_repo_id
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        print(f"\n[+] Updated models/manifest.json with repo_id: {models_repo_id}")

    config_path = repo_root / "backend" / "app" / "core" / "config.py"
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8")
        if 'MODEL_REPOSITORY: str = "privacy-eye/privacy-eye-models"' in content:
            content = content.replace(
                'MODEL_REPOSITORY: str = "privacy-eye/privacy-eye-models"',
                f'MODEL_REPOSITORY: str = "{models_repo_id}"'
            )
            config_path.write_text(content, encoding="utf-8")
            print(f"[+] Updated backend config with MODEL_REPOSITORY = {models_repo_id}")

    print("\n" + "=" * 70)
    print("ALL DATASETS & MODELS DECOUPLED & UPLOADED TO HUGGING FACE")
    print("=" * 70)
    print(f"Models Repository : https://huggingface.co/{models_repo_id}")
    print(f"Dataset Repository: https://huggingface.co/datasets/{datasets_repo_id}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
