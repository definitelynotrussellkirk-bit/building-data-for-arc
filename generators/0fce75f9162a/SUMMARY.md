# 0fce75f9162a

0-bg grid with N (2-4) connected non-bg components ('blobs'), each in its own color, occupying disjoint column ranges so they can each slide up independently without collision. Rule: for each blob, compute its bbox top row r0. Shift the blob UP by r0 rows (so its new bbox top is at row 0), preserving columns and shape. Output is a fresh grid with all blobs slid to touch the top border.

Kind: `per_puzzle`. Imported version: `1.2.1`.
Approval is derived by the catalog from current code and retained evidence.
