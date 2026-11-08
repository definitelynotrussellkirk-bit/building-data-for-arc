# 1b9e8a54331b

On a zero background, isolated color-2 seeds emit horizontal color-7 rays and
isolated color-1 seeds emit vertical color-8 rays. Color-5 line segments block
rays and remain unchanged; intersections of the two ray families become color 6.
All other cells become 0.

Version `3.0.0` uses constructive ordinary layouts. Every ordinary draw includes
both a crossing and an observable wall-stop consequence, so a three-example
lesson cannot silently teach either “ignore crossings” or “ignore walls.” The
public exact controls are `grid_h=7..14`, `grid_w=8..14`,
`horizontal_seed_count=1..2`, `vertical_seed_count=1..2`, and
`block_axis=horizontal|vertical`. Three explicitly named `texture` values are
reserved for diagnostic degenerates.

Kind: `per_puzzle`. Rule hash: `db20de981b4f`. Selected source SHA-256:
`6c473f114b9933795919e6cfdc01f60f9bfd54bfa73b03ff3d8454ebd128dae0`.
Approval and training admission remain maintainer decisions.
