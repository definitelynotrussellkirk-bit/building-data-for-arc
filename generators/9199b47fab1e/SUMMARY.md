# 9199b47fab1e

One to three color-2 seeds occupy canonical-scale chambers bounded by a single
wall color from 6, 7, 8, or 9. Cardinal BFS may traverse only colors 0 and 2;
reachable cells become 3/4/5 according to shortest-path distance modulo three,
while walls and unreachable regions stay unchanged.

Version `3.0.0` replaces random short bars with closed chamber geometry, exact
observable controls (`shape`, `n_seeds`, `wall_color`), a strict validator, and
an executable two-rival semantic contract. Every generated input makes wall
blocking answer-changing. The three-slot wall-color curriculum (`8, non-8,
non-8`) also refutes the canonical-fitting shortcut that treats only color 8 as
a barrier, including every hold-one-out query rotation of a four-pair lesson.

Kind: `per_puzzle`. Canonical rule hash: `b0749d721740`.
Approval is derived by the catalog from current code and retained evidence.
