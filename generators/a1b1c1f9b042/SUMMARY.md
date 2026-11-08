# `a1b1c1f9b042` — stable row packing (`2.0.0`)

Pack every row’s nonzero cells flush left **without changing their left-to-right order**. The generator samples inputs only; canonical Racket rule hash `8cd149b15ecf` remains the labeling authority.

The repaired default schedule alternates canonical `3×6`, canonical `4×5`, and extended profiles. Its exact public controls are `grid_h` (`2..8`), `grid_w` (`4..10`), and `palette_size` (`2..9`). Every default sample includes a shifted descending color pair, so ascending-sort-then-pack is visibly wrong in the demonstrations.

Focused status: 70 tests passed; all 11 native source-bound gates passed; an independent 108-input probe matched canonical Racket exactly. The generator is still unapproved and not admitted to training by this review.
