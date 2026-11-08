# 99d5bc858270

A 0-background grid contains exactly one yellow (4) border light and one or more non-yellow interior caster cells. The light may be on any edge or corner; at corners, the selected rule gives left/right borders priority. The canonical Racket rule clears the light and casts a yellow ray from every caster away from the light, preserving all caster cells. Generated scenes deliberately include separated collinear casters so a canonical-fitting “keep only the farthest caster per projection” shortcut is visibly wrong.

Exact controls: `grid_h=6..15`, `grid_w=7..16`, and `light_position=0..7` (top, right, bottom, left, top-left, top-right, bottom-right, bottom-left). Every exact value is supported in every difficulty band; defaults retain the full domain while weighting canonical 6×9 scale.

Kind: `per_puzzle`. Reviewed version: `3.1.1`. Canonical rule hash: `e48cc46570d0`.
Approval is derived by the catalog from current code and retained evidence.
