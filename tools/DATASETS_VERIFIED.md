# Verified public datasets for Privacy Eye (live-scan, deepfake, audio)

Compiled 2026-11-07 from official project pages, official repositories and original papers.
Every field below is tagged **VERIFIED** (read on an official source this session) or **UNVERIFIED**
(not confirmed; re-check before relying on it). Nothing here is downloaded or redistributed:
all access must go through each dataset's official channel and terms.

**Read this first**
- These are public research datasets. Most are licensed for **non-commercial research only**.
  Using them to train or tune a model in a commercial product may breach their terms. Get legal review.
- None of them is captured with Privacy Eye's pipeline (browser webcam, 640x480, JPEG q0.85,
  ~4.5 FPS). Results are **domain-shifted**: use them to measure per-signal discrimination (AUROC)
  and to find broken signals, NOT to set production thresholds on their own.
- Public datasets do not contain real-time face-swap output of the Deep-Live-Cam kind. Recordings
  from consenting people remain necessary for that attack type.
- Access realities: several datasets need an End-User License Agreement signed by someone with a
  permanent institutional position. An individual cannot sign these.

---

## A. Presentation attacks (print / screen replay) - unblocks live-scan Phase 2B/3

### A1. OULU-NPU
- Official page: https://sites.google.com/site/oulunpudatabase (VERIFIED)
- Content (official page, VERIFIED): 4,950 real-access and attack videos, 55 subjects, front cameras of
  6 phones, 3 sessions with different lighting/backgrounds. Attacks: print (2 printers) and
  video-replay (2 displays). Subject-disjoint train/dev/test. Four official protocols (I-IV).
  Discrepancy note: FG 2017 paper states 5,940 videos; website states 4,950.
- Access (VERIFIED): sign and send EULA; must be signed by a person with a permanent position at
  an institute; emails from public domains (gmail, yahoo, hotmail) are NOT accepted; download link emailed upon approval.
- License (VERIFIED): governed by EULA; strictly non-commercial academic research.
- Why useful: genuine phone-camera live videos plus real print/replay attacks; official protocols for
  generalisation (unseen lighting, attack type, camera).
- Eval mapping: real -> `real/`, print -> `attack_print/`, video-replay -> `attack_screen/`.
  Take file-naming/label rules from the dataset's own protocol files. Do not guess.

### A2. Replay-Attack (Idiap)
- Official page: https://www.idiap.ch/en/dataset/replay-attack (VERIFIED, redirected from /dataset/replayattack)
- Zenodo record: https://zenodo.org/records/4593128 (VERIFIED, updated to modern /records/ URL; DOI: 10.34777/gmc4-v249)
- Content (VERIFIED): 1,300 video clips, 50 clients; photo and video attacks (print, iPhone screen,
  iPad screen); two lighting conditions (controlled, adverse); fixed-support and hand-held attacks. Real accesses recorded with
  a MacBook built-in webcam, 320x240, Motion JPEG .mov, ~25 fps. Train/devel/test client-disjoint.
  Face-location annotations provided.
- Access (VERIFIED): Zenodo access request; requires Idiap End-User License Agreement; use strictly restricted to non-commercial research;
  the authorised signatory must hold a permanent institutional position.
- Why useful: genuine laptop-webcam live videos, the closest public match to a browser webcam, plus
  hand-held vs fixed attacks (hand-held shake relates to the jitter finding in our tests).
- Eval mapping: real -> `real/`, print -> `attack_print/`, mobile + highdef (screen) -> `attack_screen/`.

### A3. CelebA-Spoof
- Official page: https://mmlab.ie.cuhk.edu.hk/projects/CelebA/CelebA_Spoof.html (VERIFIED)
- Official repository: https://github.com/ZhangYuanhan-AI/CelebA-Spoof (VERIFIED, redirected from Davidzhangyuanhan/CelebA-Spoof)
- Paper: https://arxiv.org/abs/2007.12342 (VERIFIED)
- Content (VERIFIED): 625,537 IMAGES (not video), 10,177 subjects, 43 attributes, spoof types
  annotated (print, replay, 3D, paper cut), 8 scenes (2 environments x 4 illumination conditions),
  more than 10 sensors. Live images are taken from CelebA.
- License (VERIFIED): non-commercial research and educational purposes only; no reproduction,
  redistribution or commercial exploitation of images or derived data.
- Access / Delivery (VERIFIED): Download section hosts direct links on Google Drive (folder ID: `1OW_1bawO79pRqdVEVmBzp8HSxdSwln_Z`)
  and Baidu Drive (`https://pan.baidu.com/s/12qe13-jFJ9pE-_E3iSZtkw`, extraction password: `61fd`).
- Limitation: single images, so temporal/blink logic cannot be tested. Good for per-frame signals
  (moire, seam, screen-bezel). Live images are celebrity photos, not live webcam frames.

---

## B. Face-swap / deepfake video - for face-swap score and verdict gating

### B1. FaceForensics++ (+ Google/Jigsaw DeepFakeDetection)
- Official repository: https://github.com/ondyari/FaceForensics (VERIFIED)
- Terms of Use: http://kaldir.vc.in.tum.de/FaceForensics/webpage/FaceForensics_TOS.pdf (VERIFIED)
- Content (VERIFIED): 1,000 original video sequences manipulated with Deepfakes, Face2Face, FaceSwap,
  NeuralTextures (plus FaceShifter added later). Also hosts Google/Jigsaw Deep Fake
  Detection dataset (over 3,000 manipulated videos, 28 actors).
- Access (VERIFIED): fill Google Form (`https://docs.google.com/forms/d/e/1FAIpQLSdRRR3L5zAv6tQ_CKxmK4W96tAab_pfBu2EKAgQbeDVhmXagg/viewform`);
  upon acceptance, link to python download script (`download_faceforensics.py`) is emailed.
- License (VERIFIED): FaceForensics Terms of Use (non-commercial research only); code under MIT.
- Limitation: offline manipulations of YouTube videos, not live webcam swaps.
- Eval mapping: original -> `real/` (caveat: YouTube, not live webcam), manipulated -> `attack_faceswap/`.

### B2. Celeb-DF (v2)
- Official repository: https://github.com/yuezunli/celeb-deepfakeforensics (VERIFIED)
- Project page: https://cse.buffalo.edu/~siweilyu/celeb-deepfakeforensics.html (VERIFIED)
- Paper: https://arxiv.org/abs/1909.12962 (VERIFIED)
- Content (VERIFIED): 590 real videos (YouTube, 59 celebrities), 300 additional YouTube-real videos, and 5,639 DeepFake videos (Celeb-synthesis).
- Access (VERIFIED): Google Form (`https://forms.gle/2jYBby6y1FBU3u6q9`) or Tencent form (`https://wj.qq.com/s2/8540155/b5d9/`); download link sent upon approval.
- Rights caveat (VERIFIED): released under "Terms to Use Celeb-DF". Third-party benchmark (DeepfakeBench) lists Celeb-DF-v2 as "Rights Cleared: NO"
  because original celebrity videos are pulled from YouTube without explicit rights clearances. High licensing risk for commercial production.
- Eval mapping: Celeb-real -> `real/`, Celeb-synthesis -> `attack_faceswap/`.

### B3. DeeperForensics-1.0
- Official repository: https://github.com/EndlessSora/DeeperForensics-1.0 (VERIFIED)
- Project page: https://liming-jiang.com/projects/DrF1/DrF1.html (VERIFIED)
- Paper: https://arxiv.org/abs/2001.03024 (VERIFIED)
- Content (VERIFIED): 60,000 videos (48,475 source videos + 11,000 manipulated videos), 17.6 million frames; source videos from 100 paid actors across
  26 countries who signed consent agreements for use and manipulation of their faces; many-to-many DF-VAE face swap; 7 real-world distortion types at 5 levels.
- Disk requirement (VERIFIED): Source ~164 GB, Manipulated ~119 GB, Lists ~6.2 MB. Total ~284 GB (300 GB recommended).
- License (VERIFIED): non-commercial research only; governed by Terms of Use (`Terms_of_Use.pdf`).
- Access (VERIFIED): read Terms of Use, fill Google Form (`https://docs.google.com/forms/d/e/1FAIpQLSe6YIdIjpuL3ACdNjklZNMXXg-1csU02iO4sM7eFwkga0npVg/viewform?usp=sf_link`).
  Educational email (*.edu* preferred) recommended. Contact: `deeperforensics@gmail.com`.
- Why useful: consented actors; varied skin tones; distortions resemble real-world transmission/compression.

### B4. DFDC (Meta / Kaggle Deepfake Detection Challenge)
- Paper: https://arxiv.org/abs/2006.07397 (VERIFIED)
- Kaggle competition page: https://www.kaggle.com/c/deepfake-detection-challenge/data (VERIFIED)
- Content (VERIFIED in paper and Kaggle data): >100,000 clips from 3,426 paid actors who consented to face manipulation;
  Deepfake, GAN-based, and non-learned methods; varied settings and domestic webcam/phone backgrounds.
- Disk requirement (VERIFIED): ~470 GB training videos (50 zip parts: `dfdc_train_part_00.zip` .. `49.zip`), ~4 GB preview/test set.
- Access & Host (VERIFIED): hosted directly on Kaggle. Accessible to any individual with a standard Kaggle account by clicking "I Understand and Accept"
  on the Kaggle Competition Rules tab. Downloadable via Kaggle API: `kaggle competitions download -c deepfake-detection-challenge`.
  No institutional affiliation or academic email is required.
- License (VERIFIED): DFDC Competition Rules; non-commercial research use only.
- Why useful: realistic home/office backgrounds with consenting real people, plus swaps. Fastest large-scale deepfake dataset to obtain.

---

## C. AI-generated faces and real-face counterparts (image pipeline)

### C1. DiffusionFace
- Paper: https://arxiv.org/abs/2403.18471 (VERIFIED)
- Repository: https://github.com/Rapisurazurite/DiffFace (VERIFIED)
- Content (VERIFIED in abstract & repository): diffusion-based face forgery dataset with 11 diffusion models;
  unconditional and text-guided generation, Img2Img, inpainting, diffusion-based face exchange; metadata, plus real-world internet forged-face set.
- Access / Delivery (VERIFIED): hosted on Zenodo in two parts: DiffFace-part1 (`https://zenodo.org/records/10865300`) and DiffFace-part2 (`https://zenodo.org/records/10865065`).
- License & Terms (VERIFIED): repository specifies `license: None`. README states: "This dataset is for research purposes only" with a takedown clause for individual privacy.
  No commercial grant or standard OSI/Creative Commons license.

### C2. FFHQ (Flickr-Faces-HQ) - REAL faces
- Official repository: https://github.com/NVlabs/ffhq-dataset (VERIFIED)
- Content (VERIFIED): 70,000 PNG images, 1024x1024, crawled from Flickr; aligned and cropped.
- License (VERIFIED): dataset index, metadata and scripts under Creative Commons BY-NC-SA 4.0 by NVIDIA Corporation. Individual
  photos carry their own Flickr licenses (CC BY 2.0, CC BY-NC 2.0, Public Domain Mark 1.0, CC0 1.0 or US Government Works) recorded in JSON metadata.
- Access / Delivery (VERIFIED): hosted directly on Google Drive:
  - Metadata `ffhq-dataset-v2.json`: 255 MB
  - Thumbnails 128x128 (`thumbnails128x128`): 1.95 GB
  - Full PNG images 1024x1024 (`images1024x1024`): 89.1 GB
  Accessible directly without sign-up forms.
- Use: bona fide still faces for image-pipeline evaluation; pair with a generator's output only after dataset bias audit (format, resolution, and compression).

---

## D. Audio deepfakes (audio pipeline)

### D1. ASVspoof 2019 (LA and PA)
- Official data page: https://datashare.ed.ac.uk/items/31074a11-b6f6-4e92-a4ad-07093f8c0c45 (VERIFIED, redirected from /handle/10283/3336; DOI: 10.7488/ds/2555)
- Content (VERIFIED): logical-access (TTS/voice-conversion; 17 systems) and physical-access (simulated replay) partitions;
  bona fide and spoof labels; train/dev/eval speakers 20/10/48; derived from the VCTK corpus. Files: LA.zip ~7.1 GB, PA.zip ~16.4 GB.
- License (VERIFIED): Open Data Commons Attribution License (ODC-By). Freely available for academic and commercial purposes with attribution.
- Access (VERIFIED): direct public bitstream download from Edinburgh DataShare without login, form, or institutional barrier.
- Limitation: studio-quality speech, not browser microphone audio; evaluates heuristic audio features only.

---

## E. Considered but NOT verified this session (do not use until verified)
SiW, SiW-M, CASIA-FASD, CASIA-SURF, MSU-MFSD, WildDeepfake, FakeAVCeleb, DeepFake-TIMIT, UADFV,
GenImage, and Kaggle "real and fake faces" mirrors. Mirrors and re-uploads (Kaggle, Baidu, torrents,
Hugging Face copies) may violate original terms: use official channels only.

---

## F. Fastest realistic order for a solo developer
1. **Direct, no agreement signing:**
   - ASVspoof 2019 (audio, ODC-By, direct download from Edinburgh DataShare)
   - FFHQ (real still faces, Google Drive direct download, CC BY-NC-SA 4.0)
   - CelebA-Spoof (spoof still images, Google Drive direct download, non-commercial)
2. **Kaggle account (instant access via web acceptance):**
   - DFDC (Meta/Kaggle, ~470 GB, accepted directly with personal Kaggle account, non-commercial)
3. **Request forms, approval required, non-commercial terms:**
   - FaceForensics++ (Google Form, download script emailed)
   - DeeperForensics-1.0 (Google Form, *.edu* email preferred, ~284 GB)
   - Celeb-DF v2 (Google / Tencent form, YouTube copyright caveat)
4. **Institution required:**
   - OULU-NPU (EULA signed by permanent faculty/staff, academic email required)
   - Replay-Attack (Zenodo access request + Idiap EULA signed by permanent faculty/staff)
5. **Always needed:**
   - Real pipeline recordings of consenting people (captured per `tools/DATA_COLLECTION.md`), including live face-swap attacks. Public data cannot replace these for final production calibration.

## G. Mapping to the eval_live_scan.py folder layout
| Folder | Public sources (video unless noted) |
|---|---|
| `real/` | Replay-Attack real accesses, OULU-NPU real, DFDC real, FF++ originals, Celeb-real |
| `attack_screen/` | Replay-Attack mobile/highdef, OULU-NPU video-replay, CelebA-Spoof replay (images) |
| `attack_print/` | Replay-Attack print, OULU-NPU print, CelebA-Spoof print (images) |
| `attack_faceswap/` | FaceForensics++, Celeb-DF synthesis, DeeperForensics-1.0, DFDC fakes |
| `attack_ai/` | DiffusionFace (images) |
