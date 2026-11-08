# Working notes: aa2b217615f3

## Current decision

Version `2.2.0` repairs the ordinary sampler so every nondegenerate lesson contains two same-lane one-cell objects at depths 2 and 4. Their collision forces genuine stacking and prevents an ordinary lesson from being explained by independent sliding. The canonical transformation and shared authority are unchanged.

The native parametric family uses matched inputs with `stack_order = near_first | far_first`; `near_first` is the exact canonical default. Each setting supports 2–6 demonstrations and four sequentially projected queries. The protected witness for `far_first` commits the farthest object first, then shows later stopping positions depend on that occupied-cell intermediate.

The strongest canonical-fitting shape shortcut found in this review is “fill every object bounding box, then slide.” It matches all three canonical demonstrations because their objects are rectangular, but the repaired generator still emits nonrectangular L-shapes; seed 0/sample 2 gives a protected-Racket-confirmed disagreement in `checks/aa2b217615f3/shortcut-rival/report.json`.

Reviewer checks are finite rather than universal: 26 focused tests, 96 protected Racket audit evaluations, 64 audit seeds, the cross-family 512-seed fuzz pass, public projection/privacy checks, and a 30x30 stress case. Next useful action is owner-side native qualification and fresh acceptance against these exact source hashes. No variant approval, owner acceptance, or training admission is claimed.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/aa2b217615f3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
