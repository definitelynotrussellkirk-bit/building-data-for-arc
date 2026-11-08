# 42a0c35b41fd

0-bg grid (h ∈ 8-11, w ∈ 9-12) with: (a) ONE CORNER KEY at FIXED position (0, 0) — value ∈ {1..7} selecting a transform (per demos: 1=identity, 2=cw90, 3=180, 4=ccw90, 5=flip-LR, 6=flip-UD, 7=transpose); (b) ONE LARGE NON-CORNER BLOB — an irregular 4-5 cell blob in palette[0] (a non-key color drawn from {1..9}\{key}) built by grow_blob random walk, placed away from (0, 0); (c) ONE SMALLER DECOY BLOB — a 2-cell blob in palette[1] (distinct from key + primary), placed to add visual noise but smaller than the primary. Rule (READ THE CORNER KEY, FIND THE LARGEST NON-CORNER BLOB, TRANSFORM IT BY THE KEY, CROP, OUTPUT): READ key from (0, 0) → select transform. EXTRACT every non-bg blob excluding the key cell. FIND the LARGEST blob (by cell count). CROP it to its bbox. APPLY the key's transform (identity / cw / 180 / ccw / flip_lr / flip_ud / transpose). OUTPUT the transformed crop. Net: the corner key picks one of 7 dihedral operations to apply to the cropped largest blob; smaller blobs are discarded.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
