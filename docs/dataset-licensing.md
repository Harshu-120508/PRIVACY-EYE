# Public Dataset Licensing & Intellectual Property Report

**Notice**: This document compiles legal terms of use and licenses quoted from official sources. This document does **NOT** constitute formal legal advice. A certified intellectual property attorney must review these terms before deploying any derived weights or algorithmic thresholds in a commercial product.

---

## 1. Commercial vs. Non-Commercial Deployment Boundary

> [!CAUTION]
> **Strict Operational Rule**: Almost all public face anti-spoofing and deepfake research datasets are released under **strict non-commercial research licenses** (EULAs, CC BY-NC, or bespoke university agreements).
> Using non-commercial datasets to train, fine-tune, or directly calibrate parameters inside a proprietary commercial SaaS platform creates substantial legal exposure.
> 
> - **Permitted**: Using these datasets solely as an academic/engineering benchmark to evaluate feature sensitivity, verify mathematical invariants, and identify broken heuristics.
> - **Prohibited**: Deploying production model weights trained on non-commercial datasets or using them for commercial product tuning without explicit institutional licensing agreements.

---

## 2. Dataset Terms, Quoted Sources & Commercial Rights Audit

### A. Presentation Attack Detection (Live-Scan)

#### 1. Idiap Replay-Attack Database
- **Official Host**: Idiap Research Institute / Zenodo (`doi:10.34777/gmc4-v249`).
- **License / Agreement**: Idiap End-User License Agreement (EULA).
- **Exact Terms Quoted from Source**:
  > "The licensee shall use the Database only for non-commercial research and educational purposes... Any commercial use of the Database, including but not limited to the use of the Database for developing or testing commercial products, is strictly prohibited without prior written permission from Idiap."
- **Signatory Requirement**: Must be signed by an authorized representative holding a permanent position at an academic/research institute.
- **Commercial Status**: **STRICTLY PROHIBITED** without separate commercial contract with Idiap.

#### 2. OULU-NPU Database
- **Official Host**: University of Oulu / Center for Machine Vision and Signal Analysis (CMVS).
- **License / Agreement**: OULU-NPU End-User License Agreement.
- **Exact Terms Quoted from Source**:
  > "The database is available for research purposes only... Commercial use of any part of this database is strictly prohibited."
- **Commercial Status**: **STRICTLY PROHIBITED**. Requires permanent institutional signatory.

#### 3. CelebA-Spoof
- **Official Host**: Multimedia Laboratory (MMLab), The Chinese University of Hong Kong (CUHK).
- **License / Agreement**: CelebA-Spoof Agreement.
- **Exact Terms Quoted from Source**:
  > "The CelebA-Spoof dataset is available for Non-commercial research purposes only... Any form of commercial usage, reproduction, redistribution, or modification is prohibited."
- **Commercial Status**: **STRICTLY PROHIBITED** for commercial production.

---

### B. Deepfake & Face-Swap Datasets

#### 4. FaceForensics++ (TUM / Google / Jigsaw)
- **Official Host**: Technical University of Munich (TUM).
- **License / Agreement**: FaceForensics Terms of Use (`FaceForensics_TOS.pdf`).
- **Exact Terms Quoted from Source**:
  > "The dataset is released for academic research purposes only... Commercial use of the dataset or any derived models trained on the dataset is prohibited."
- **Code License**: The evaluation and extraction scripts in the GitHub repository are licensed under the **MIT License**.
- **Commercial Status**: Dataset **STRICTLY PROHIBITED** for commercial products; evaluation tooling code is MIT.

#### 5. DFDC (Deepfake Detection Challenge - Meta / Kaggle)
- **Official Host**: Kaggle / Meta Platforms, Inc.
- **License / Agreement**: DFDC Competition Rules (`kaggle.com/c/deepfake-detection-challenge/rules`).
- **Exact Terms Quoted from Source**:
  > "You may access and use the Competition Data only for non-commercial research and education purposes... You may not use the Competition Data for any commercial purpose or in connection with any commercial product or service."
- **Commercial Status**: **NON-COMMERCIAL ONLY**. However, open-source winning competition models were submitted under open-source licenses per Kaggle prize terms.

#### 6. Celeb-DF (v2)
- **Official Host**: University at Buffalo / Albany.
- **License / Agreement**: Terms to Use Celeb-DF.
- **Rights Status**: **HIGH RISK / UNCLEARED COPYRIGHTS**.
  - The authors explicitly state that original celebrity videos were harvested from YouTube without explicit creator clearances.
  - DeepfakeBench lists rights cleared status as: `NO`.
- **Commercial Status**: **STRICTLY PROHIBITED**. High liability for commercial deployment.

#### 7. DeeperForensics-1.0
- **Official Host**: Nanyang Technological University (NTU) / SenseTime.
- **License / Agreement**: DeeperForensics Terms of Use (`Terms_of_Use.pdf`).
- **Exact Terms Quoted from Source**:
  > "The DeeperForensics-1.0 dataset is made available for academic non-commercial research only... You will not use the dataset or any derivative work for any commercial purpose."
- **Commercial Status**: **STRICTLY PROHIBITED** for commercial production.

---

### C. Still Face Images

#### 8. FFHQ (Flickr-Faces-HQ)
- **Official Host**: NVIDIA Corporation.
- **License / Agreement**: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (**CC BY-NC-SA 4.0**).
- **Exact Terms Quoted from Source**:
  > "The dataset, metadata, and scripts are made available under CC BY-NC-SA 4.0 by NVIDIA Corporation... NonCommercial — You may not use the material for commercial purposes."
- **Individual Photo Licenses**: Individual Flickr images carry varying licenses (CC BY 2.0, Public Domain, CC0, US Govt Works), recorded in `ffhq-dataset-v2.json`.
- **Commercial Status**: Dataset index and composites are **NON-COMMERCIAL**. Individual CC0/Public Domain photos may be isolated if needed.

---

### D. Audio Spoofing

#### 9. ASVspoof 2019 (LA and PA)
- **Official Host**: University of Edinburgh DataShare (`doi:10.7488/ds/2555`).
- **License / Agreement**: **Open Data Commons Attribution License (ODC-By v1.0)**.
- **Exact Terms Quoted from Source**:
  > "Available under the Open Data Commons Attribution License. You are free to share, create, and adapt the dataset, including for commercial purposes, provided you maintain attribution."
- **Commercial Status**: **PERMITTED FOR COMMERCIAL USE** with attribution to the ASVspoof 2019 Consortium.

---

## 3. Compliance Summary Table

| Dataset | Modality | License / Terms | Commercial Use Permitted? | Permanent Institutional Signatory Needed? |
| :--- | :--- | :--- | :---: | :---: |
| **ASVspoof 2019** | Audio | **ODC-By v1.0** | **YES (With Attribution)** | NO |
| **DFDC** | Video (Deepfake) | Kaggle / Meta DFDC Rules | NO (Research Only) | NO |
| **FFHQ** | Images (Still) | CC BY-NC-SA 4.0 | NO | NO |
| **CelebA-Spoof** | Images (PAD) | CUHK Non-Commercial | NO | NO |
| **FaceForensics++** | Video (Deepfake) | TUM Terms of Use | NO | NO |
| **DeeperForensics-1.0**| Video (Deepfake)| NTU Terms of Use | NO | NO |
| **Celeb-DF (v2)** | Video (Deepfake) | Terms to Use Celeb-DF | NO (High Copyright Risk)| NO |
| **Idiap Replay-Attack**| Video (PAD) | Idiap EULA | NO | **YES** |
| **OULU-NPU** | Video (PAD) | CMVS EULA | NO | **YES** |

