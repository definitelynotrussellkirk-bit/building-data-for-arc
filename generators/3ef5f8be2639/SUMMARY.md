# 3ef5f8be2639

Version `4.0.0`; canonical Racket rule hash `020757caefaf`.

Select the first color-2 cell and the first color-3 cell in row-major order. Grow each selected center to its full 3×3 Chebyshev-radius-1 neighborhood, intersect those neighborhoods, and paint the intersection color 8 on an otherwise blank canvas of the same shape. Later color-2/3 cells are distractors; the rule ignores them.

The constructive sampler exposes only recoverable exact controls: `grid_h` and `grid_w` in 7..14, all 24 relative offsets at Chebyshev distance 1 or 2, and one or two cells of each seed color. The default schedule supplies 7×7/8×8 canonical profiles in every difficulty band, alternates distance-1 and distance-2 selected pairs, and puts an effective scan-order distractor in every even-indexed draw.

Task-local semantic contracts declare two canonical-fitting rivals: grow every 2/3 pair, and solve only distance-2 cases. The production lesson census and cyclic-rotation probe require each lesson to refute both.

Final checked generator SHA-256: `c5e2f143ecdc72ef4195f54a18c009f4e4c2e75dd3a9ff041622b1d394bd84b5`. The selected Racket authority and canonical ledger were not changed.
