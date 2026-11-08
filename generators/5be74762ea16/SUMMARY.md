# 5be74762ea16

0-bg grid (h×w, ~9-11 by ~10-12) with exactly 3 connected BLOBS in distinct non-zero colors and STRICTLY DISTINCT cell counts (e.g., 2, 4, 8). Blobs 8-conn isolated. The MEDIAN-size blob (the middle one by cell count) has a NON-SQUARE bbox so the h>w branch is triggerable. Rule: sort blobs by cell count ascending. Pick the MIDDLE one (median). Crop to its bbox (preserving holes as 0). If bbox h > w, rotate the crop 90° clockwise. Else output as-is. Output = the (possibly rotated) cropped median blob.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
