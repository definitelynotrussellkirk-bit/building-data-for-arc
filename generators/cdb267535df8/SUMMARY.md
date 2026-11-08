# cdb267535df8 — Wall-Geodesic Voronoi

Version: `2.0.0`. Canonical pin: `cb6c4f271562` (unchanged Racket authority).

Sample 4–6 seed cells of 2–4 non-wall colors among varied color-5 barriers.
Fill empty cells using cardinal shortest-path distance, treating equal-distance
seeds of the same color as one winning color. Different-color ties and
unreachable blanks remain zero; all existing nonzero cells are preserved.

The prior version described and generated contact-degree recoloring, a different
task. This replacement realigns the input distribution and validation to the
selected canonical rule. It does not alter catalog approval or training admission.

Defaults use two repeated-color witness profiles in each four-draw cycle, so
three-demo/one-query lessons retain a same-color counterexample under any query
rotation. Every sampled input also refutes wall-ignoring, diagonal-distance and
lowest-color tie-breaking rivals. See `notes.md`, `workspace/README.md`, and
`tests/test_voronoi.py` for the finite scope and exact controls.
