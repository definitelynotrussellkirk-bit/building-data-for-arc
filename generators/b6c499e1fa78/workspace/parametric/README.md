# `b6c499e1fa78` parametric family

`branch_policy=unconditional` is the exact canonical match-or-branch rule.

`branch_policy=matched_area` is sequential:

1. **A — fit locks:** identify every gray key whose top rows match a blue-wall opening, including reflection.
2. **Intermediate:** the set of full occupied areas of those matching keys. The constructed keys extend below their opening-shaped top slice, so this is not opening area or bounding-box area.
3. **B — gate branches:** matching keys always turn red; a branched key turns red only if its full occupied area is in the intermediate set.

The four queries remain private controller-side and `public_turn()` exposes one input at a time without settings, programs, answers, future inputs, turn index, or total-count hints.
