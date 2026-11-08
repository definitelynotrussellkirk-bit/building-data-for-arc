# 39fd645f21c6 parametric family

`match_policy=exact_triple` is the exact canonical program.
`match_policy=best_partial` computes the blue seed's `(area, holes, symmetry)`
triple, counts mismatching coordinates for every candidate, finds the global
minimum, and recolors every candidate attaining that minimum cyan.

The first demonstration has no exact match and three different one-coordinate
near matches. The second has an exact different-shape twin, forcing the
best-partial rule to prefer mismatch zero over the near matches. Inputs are
setting-independent and the four query surfaces end in a dense 30×30 scene.
