# 95315dd52287

0-bg grid (h×w, ~6-9 by ~7-10) containing: (a) a 2-color BLOB (a few connected cells in 2 distinct non-{0,8} colors) placed in the upper-left area; (b) exactly ONE color-8 (cyan) ANCHOR cell placed elsewhere, with room for the blob's bbox to fit when re-anchored. Rule: detect the color-8 anchor (must be exactly 1). Detect all non-{0,8} cells (the blob). Crop the blob to its bbox. Build a fresh 0-canvas. Paste the cropped blob such that its top-left corner aligns with the anchor position. Output: blob translated to anchor; original blob position cleared.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
