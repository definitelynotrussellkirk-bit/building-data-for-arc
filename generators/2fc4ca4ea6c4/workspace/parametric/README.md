# Midpoint completion family — 2fc4ca4ea6c4

`completion_mode` is fixed for an episode:

- `midpoints` is the exact selected canonical rule: every same-color horizontal
  run is reduced to its midpoint.
- `connect_aligned` first performs that collapse, then connects exactly two
  equal-colored midpoint cells aligned in a column across empty space.

Inputs are matched across settings. The two-demo minimum includes singleton
runs, longer runs, aligned equal-color pairs, a blocked equal-color pair, and a
three-endpoint same-color column. Those last two cases teach the clear-path and
exactly-two guards rather than leaving them as unobserved implementation details.
Four query profiles include a substantive 30×30 case whose runs touch all four
boundaries.

Sequential dependency: **A** computes the input-dependent midpoint grid. That
exact grid is the intermediate. **B** detects aligned same-color endpoints in
that intermediate and fills the vertical segment. Running B on the original
wide runs produces bands and therefore changes the final output; skipping B
leaves only midpoint dots.
