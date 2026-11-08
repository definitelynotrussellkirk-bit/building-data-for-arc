# 97e4de6b44f4

0-bg grid (h×w, ~4-6 by ~6-9) with: (a) one MARKER cell in color 8 (cyan) or 9 (maroon) placed at the top of the grid; (b) one connected non-rectangular BLOB of 3-4 cells in some color ≠ {0, 8, 9}, placed below the marker. Rule: detect marker color. Extract blob, crop to bbox. If marker == 8, apply rotate-cw; else (marker == 9), apply flip-lr. Output = transformed cropped blob.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
