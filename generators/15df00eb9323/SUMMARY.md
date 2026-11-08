# 15df00eb9323

3 isolated distinct-color blobs on a 0-bg grid, similar in size. Rule crops each blob to its bbox, then computes a max(h)×max(w) overlay: at each (r, c), count how many blob crops have a non-zero at that cell. Output is bbox-cropped to non-zero of: 8 where count ≥ 2, else 0.

Kind: `per_puzzle`. Imported version: `1.3.0`.
Approval is derived by the catalog from current code and retained evidence.
