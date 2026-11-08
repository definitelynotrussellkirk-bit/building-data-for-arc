# c2996845ede0

0-bg grid (h~6-12, w~10-16) with: (a) ONE LARGE ASYMMETRIC OBJECT (4-8 cells) drawn from a hand-curated shape bank in some big_color; (b) 1-(big_size-2) ISOLATED SINGLETON CELLS as distractors in a different small_color. The big object is strictly larger than all singletons (size delta ≥2). The big object is horizontally ASYMMETRIC (so mirror differs from original). Objects are 4-conn isolated (no shared neighborhoods). Position bias varies (big_left/right/top/bottom_small or big_any). Rule: identify the LARGEST object (the big asymmetric one). NORMALIZE its cells. MIRROR HORIZONTALLY. COMPUTE the UNION (original cells ∪ mirrored cells). CROP to that union's BBOX. PAINT in the big object's color. Output: the cropped mirror-union subgrid. Singletons are discarded. Net: largest object gets symmetrized via horizontal mirror-union.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
