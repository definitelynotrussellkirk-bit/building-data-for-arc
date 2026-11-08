# 59ccf6f5cc65

Canonical-profile grids use background 0, a color-5 singleton marker at one exact
corner, and several 4-connected color-7 (orange) components. Recolor an entire
orange component to color 1 (blue) **iff one of that component's cells is exactly
one of the four grid-corner cells**. Orange components that merely touch one or
two borders, or whose bounding box contains a corner while the corner cell itself
is absent, remain orange. The color-5 marker is unchanged.

The sampler cycles through the four canonical dimension profiles `(8,9)`, `(9,10)`,
`(8,10)`, and `(9,11)`. Every ordinary draw includes a missing-corner L decoy, a
nonrectangular true-corner component, and a strictly interior component; half the
schedule includes a second true-corner component. These witnesses distinguish the
exact-cell rule from border-touch, bounding-box, rectangle-only, recolor-all, and
first-corner-only shortcuts.

Kind: `per_puzzle`. Current version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
