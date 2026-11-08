# 764b6b9e7771 — reflective beam curriculum

A red `2` source and its cardinal-adjacent blue `1` marker launch a beam. The
beam paints traversed background cells `8`, reflects from diagonal mirror
colors `4` and `6`, and stops at a gray `5` wall, the grid edge, or a repeated
position-and-direction state. The selected Racket rule remains the canonical
rule with normalized hash `b28f2ec65f40`.

Generator version `4.0.0` constructs compact serpentine routes. Every requested
mirror lies on the beam path; examples with three or more mirrors mix relative
left and right turns; an optional connected wall lies on the final ray. Exact
public controls are `grid_h=9..18`, `grid_w=12..20`, `n_mirrors=2..6`,
`n_walls=0..6`, four launch directions, and two first-turn sides.

The default mirror-count schedule cycles `2,3,4,5,6`. With
`EXAMPLES_NEEDED = 3`, every consecutive three-example lesson contains a
three-or-more-mirror case and refutes the five declared canonical-fitting
rivals. Approval and training admission remain catalog decisions; this review
does not change either.
