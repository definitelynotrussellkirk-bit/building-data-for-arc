# Parametric run projection

The byte-exact canonical default, `endpoints`, retains only the first and last
cell of every horizontal same-color run. The nearby `longest_color_gate`
variant first finds the unique longest run and uses its color as an
input-dependent intermediate. Runs of that color retain endpoints; every other
run retains its one or two central cells. Episodes guarantee that the anchor
color recurs, the first run has another color, both center parities are taught,
and the final query is a substantive 30×30 case.

The two-step dependency is causal: choosing the first run's color instead of
the unique longest run's color changes the final projection on generated cases.
Two protected-Racket demonstrations distinguish the supported setting from the
canonical, first-run-anchor, and all-centers rivals.
