# Data Access & Acquisition Plan for Privacy Eye

**Storage Rule**: All datasets must live **OUTSIDE** this repository (e.g. `D:\datasets\<dataset_name>` or `C:\privacy_eye_data\<dataset_name>`).
**Hard Rule**: Never commit data, never redistribute it, never copy it into the repository git tree.
**Legal Notice**: All listed datasets except ASVspoof 2019 are restricted to **non-commercial academic research**. They are intended to evaluate signal discrimination and domain shift, NOT for commercial model training without formal legal clearance.

---

## 1. Dataset Acquisition Tracking Table

| Dataset | Priority / Speed Tier | Signatory Requirement | Expected Size | Requested? | Approval Date | Received? | Local Path (Outside Repo) | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **ASVspoof 2019** | **Tier 1 (Instant)** | None (Public Domain / ODC-By) | 23.5 GB (LA 7.1G + PA 16.4G) | Direct | Immediate | [ ] | `D:\datasets\asvspoof2019` | Pending Download |
| **FFHQ** | **Tier 1 (Instant)** | None (CC BY-NC-SA 4.0) | 1.95 GB (128px) / 89 GB (1024px) | Direct | Immediate | [ ] | `D:\datasets\ffhq` | Pending Download |
| **CelebA-Spoof** | **Tier 1 (Instant)** | None (Google Drive link) | ~110 GB total (Images) | Direct | Immediate | [ ] | `D:\datasets\celeba_spoof` | Pending Download |
| **DFDC** | **Tier 2 (Kaggle Rules)** | Individual Kaggle Account | ~470 GB (Train) / ~4 GB (Test) | [ ] | Instant via Web | [ ] | `D:\datasets\dfdc` | Pending Acceptance |
| **FaceForensics++** | **Tier 3 (Web Form)** | Individual Researcher | ~80 GB - 400 GB (C23/C40/raw) | [ ] | 1 - 3 Days | [ ] | `D:\datasets\faceforensics` | Pending Form Submit |
| **DeeperForensics-1.0**| **Tier 3 (Web Form)** | Individual (*.edu* preferred) | ~284 GB (Source 164G + Swap 119G)| [ ] | 2 - 5 Days | [ ] | `D:\datasets\deeperforensics` | Pending Form Submit |
| **Celeb-DF (v2)** | **Tier 3 (Web Form)** | Individual Researcher | ~35 GB | [ ] | 2 - 5 Days | [ ] | `D:\datasets\celeb_df` | High Copyright Risk |
| **Replay-Attack** | **Tier 4 (Institution)**| **Permanent Faculty/Staff** | ~10 GB | [ ] | Restricted | [ ] | `D:\datasets\replay_attack` | Needs University Co-signer |
| **OULU-NPU** | **Tier 4 (Institution)**| **Permanent Faculty/Staff** | ~50 GB | [ ] | Restricted | [ ] | `D:\datasets\oulu_npu` | Needs University Co-signer |

---

## 2. Step-by-Step Manual Acquisition Instructions

### Tier 1: Instant Public Access (No Forms / No Waiting)

#### 1. ASVspoof 2019 (Audio PAD)
- **URL**: [https://datashare.ed.ac.uk/items/31074a11-b6f6-4e92-a4ad-07093f8c0c45](https://datashare.ed.ac.uk/items/31074a11-b6f6-4e92-a4ad-07093f8c0c45)
- **License**: Open Data Commons Attribution License (ODC-By). Permitted for academic and commercial use with attribution.
- **Action**:
  1. Download `LA.zip` (Logical Access: TTS/VC deepfake voice, 7.1 GB).
  2. Download `PA.zip` (Physical Access: Replay speech, 16.4 GB).
  3. Extract to outside folder: `D:\datasets\asvspoof2019\`.

#### 2. FFHQ (Bona Fide Still Faces)
- **URL**: [https://github.com/NVlabs/ffhq-dataset](https://github.com/NVlabs/ffhq-dataset)
- **License**: Creative Commons BY-NC-SA 4.0 (NVIDIA) + individual Flickr licenses in metadata JSON.
- **Action**:
  1. Open Google Drive folder: [ffhq-dataset](https://drive.google.com/open?id=1u2xu7bSrWxrbUxk-dT-UvEJq8IjdmNTP)
  2. For rapid signal evaluation, download `thumbnails128x128` (1.95 GB) or select a subset of `images1024x1024` (89.1 GB).
  3. Download metadata: `ffhq-dataset-v2.json` (255 MB).
  4. Save to `D:\datasets\ffhq\`.

#### 3. CelebA-Spoof (Per-Frame Print / Screen Spoof Images)
- **URL**: [https://github.com/ZhangYuanhan-AI/CelebA-Spoof](https://github.com/ZhangYuanhan-AI/CelebA-Spoof)
- **License**: Non-commercial research & education only.
- **Action**:
  1. Open Google Drive: [CelebA-Spoof Folder](https://drive.google.com/drive/folders/1OW_1bawO79pRqdVEVmBzp8HSxdSwln_Z?usp=sharing)
     (Alternative Baidu mirror: `https://pan.baidu.com/s/12qe13-jFJ9pE-_E3iSZtkw`, code: `61fd`).
  2. Download annotation JSON and image split archives.
  3. Save to `D:\datasets\celeba_spoof\`.

---

### Tier 2: Instant Agreement via Existing Personal Accounts

#### 4. DFDC (Deepfake Detection Challenge - Meta / Kaggle)
- **URL**: [https://www.kaggle.com/c/deepfake-detection-challenge/data](https://www.kaggle.com/c/deepfake-detection-challenge/data)
- **Signatory Requirement**: Any individual with a standard Kaggle account.
- **Action**:
  1. Log into your Kaggle account.
  2. Visit [https://www.kaggle.com/c/deepfake-detection-challenge/rules](https://www.kaggle.com/c/deepfake-detection-challenge/rules).
  3. Click **"I Understand and Accept"** to agree to the competition rules.
  4. Download via Kaggle CLI:
     ```bash
     # To download the full 470 GB training set:
     kaggle competitions download -c deepfake-detection-challenge -p D:\datasets\dfdc
     # Or download specific parts (e.g. part 00 for initial testing):
     # via Kaggle web interface: dfdc_train_part_00.zip (~10 GB)
     ```

---

### Tier 3: Researcher Google / Web Forms (Approval Required)

#### 5. FaceForensics++
- **URL**: [https://github.com/ondyari/FaceForensics](https://github.com/ondyari/FaceForensics)
- **Form Link**: [https://docs.google.com/forms/d/e/1FAIpQLSdRRR3L5zAv6tQ_CKxmK4W96tAab_pfBu2EKAgQbeDVhmXagg/viewform](https://docs.google.com/forms/d/e/1FAIpQLSdRRR3L5zAv6tQ_CKxmK4W96tAab_pfBu2EKAgQbeDVhmXagg/viewform)
- **Terms of Use**: Academic non-commercial research only.
- **Draft Request Text for Form**:
  > "I am conducting independent academic research evaluating presentation attack detection, spatial seam analysis, and deepfake face-swap discrimination under real-world webcam compression artifacts. The FaceForensics++ dataset and Google/Jigsaw DeepFake Detection videos will be used strictly for benchmarking detection heuristics and measuring domain shift on held-out test splits. All data will be stored securely and deleted after completion of the evaluation study."

#### 6. DeeperForensics-1.0
- **URL**: [https://github.com/EndlessSora/DeeperForensics-1.0](https://github.com/EndlessSora/DeeperForensics-1.0)
- **Form Link**: [https://docs.google.com/forms/d/e/1FAIpQLSe6YIdIjpuL3ACdNjklZNMXXg-1csU02iO4sM7eFwkga0npVg/viewform?usp=sf_link](https://docs.google.com/forms/d/e/1FAIpQLSe6YIdIjpuL3ACdNjklZNMXXg-1csU02iO4sM7eFwkga0npVg/viewform?usp=sf_link)
- **Terms of Use**: Academic non-commercial research only (`dataset/Terms_of_Use.pdf`). Educational email preferred.
- **Contact**: `deeperforensics@gmail.com`
- **Draft Request Text for Form**:
  > "We request access to DeeperForensics-1.0 to benchmark face anti-spoofing and deepfake swap boundary detection against transmission distortions and real-world perturbations. The dataset will reside on an encrypted local storage volume, restricted solely to non-commercial research benchmarking."

#### 7. Celeb-DF (v2)
- **Form Link**: [https://forms.gle/2jYBby6y1FBU3u6q9](https://forms.gle/2jYBby6y1FBU3u6q9)
- **Caution**: The source videos are pulled from YouTube without cleared copyrights. Use only for academic benchmark comparisons, never for commercial systems.

---

### Tier 4: Institutional Signatory Required (Permanent Position)

#### 8. Replay-Attack (Idiap)
- **URL**: [https://zenodo.org/records/4593128](https://zenodo.org/records/4593128)
- **Access Constraint**: Idiap EULA explicitly requires a signatory with a **permanent position** at an academic or research institute (e.g., Professor, Tenured Faculty, Lab Director). An individual independent developer cannot legally sign this agreement alone.
- **Action**:
  1. Partner with a university research collaborator or institutional faculty member.
  2. Have the institutional sponsor submit the access request via Zenodo with institutional credentials.

#### 9. OULU-NPU
- **URL**: [https://sites.google.com/site/oulunpudatabase](https://sites.google.com/site/oulunpudatabase)
- **Access Constraint**: EULA strictly rejects public email domains (`@gmail.com`, `@yahoo.com`, `@hotmail.com`). Must be signed by a permanent academic staff member.
- **Action**:
  1. Download EULA from the official website.
  2. Institutional signatory signs and emails from an institutional domain to the OULU-NPU contact.

---

## 3. What to Do Once Data is Downloaded

When you have saved any of these datasets to disk:
1. Note the folder path in the tracking table above (e.g. `D:\datasets\dfdc`).
2. Run the corresponding adapter from `tools/adapters/<dataset>.py` to generate the test manifest/symlinks for `evaluation/eval_live_scan.py`.
3. Execute `python evaluation/eval_live_scan.py --data <adapter_output_dir> --v2`.

