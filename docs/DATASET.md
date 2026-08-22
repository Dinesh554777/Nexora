# OAI Tissue Segmentations — Dataset Documentation (Phase 1)

## Status: DATASET NOT PRESENT ON THIS MACHINE

As of 2026-08-22 the OAI Tissue Segmentations dataset has **not been located anywhere on this
workstation**. No inspection could be performed. Nothing below is fabricated.

## Search performed (exhaustive)

Recursive filename scan of `C:\Users\hp` (depth 6) for:

- Extensions: `.nii`, `.nii.gz`, `.mha`, `.mhd`, `.dcm`, `.ima`, `.nrrd`
- Directory names matching: `oai | meniscus | knee | segmentation`

Result: only false positives (matplotlib sample data, browser-profile folders, library packages).
Also verified absent from:

- `Downloads/` (full listing, incl. archive files)
- `Desktop/`, `Documents/`, `OneDrive/`
- All project folders under `Dinesh Projects\` and `C:\Users\hp`

No Kaggle CLI config (`~/.kaggle`) exists either.

## Inspection checklist — all UNKNOWN until data is placed

| # | Question | Status |
|---|----------|--------|
| 1 | Image file format | UNVERIFIED |
| 2 | Mask file format | UNVERIFIED |
| 3 | Number of subjects | UNVERIFIED |
| 4 | Number of images | UNVERIFIED |
| 5 | Image dimensions | UNVERIFIED |
| 6 | Mask dimensions | UNVERIFIED |
| 7 | Image orientation | UNVERIFIED |
| 8 | Pixel/voxel spacing | UNVERIFIED |
| 9 | Subject IDs | UNVERIFIED |
| 10 | Knee laterality | UNVERIFIED |
| 11 | Visit information | UNVERIFIED |
| 12 | Unique mask labels | UNVERIFIED |
| 13 | Medial meniscus label | UNVERIFIED |
| 14 | Femur/tibia/other labels | UNVERIFIED |
| 15 | Metadata availability | UNVERIFIED |
| 16 | Age/sex/BMI/OA labels | UNVERIFIED |

## How to unblock Phase 1

1. Download *OAI Tissue Segmentations* manually from Kaggle into:
   `data/raw/OAI_Tissue_Segmentations/` (inside this repo; keep it git-ignored)
2. Install the missing reader dependency:
   `pip install nibabel`
3. Run the inspector (read-only):
   `python scripts/inspect_dataset.py --data-root data/raw/OAI_Tissue_Segmentations`
4. It emits `reports/dataset_inspection.json` and `reports/sample_slice.png`.
   Then fill every row above from actual output. Do not guess.

## Limitations

- Zero dataset facts can be stated yet; any meniscus-label or spacing claim would be fabrication.
- The pairing heuristic in `scripts/inspect_dataset.py` (image↔mask by name similarity) is a
  fallback and must be validated against the real folder layout once available.
