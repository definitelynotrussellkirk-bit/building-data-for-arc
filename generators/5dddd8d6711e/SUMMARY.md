# 5dddd8d6711e — shortest door path

Version `4.0.0`; canonical rule pin `5e8877987e4c`.

Rectangular chambers have independently varying row heights and column widths.
Walls are color 1 or 9, and each color-7 door links two neighboring chambers.
The color-2 and color-3 markers select endpoints. The unchanged Racket authority
uses chamber-count BFS with sorted row-major chamber IDs, preserves walls and
doors, clears nonpath interiors, and fills the chosen path with color 8.
Disconnected endpoints clear every interior; endpoints in one chamber fill it.

The default seed-rotated three-draw schedule combines an informative cyclic
maze, randomized canonical geometry, and broader variable mazes. Every three
consecutive default draws include a witness against the five declared rivals.
Exact controls are `rooms_r=1..6`, `rooms_c=1..6`, `wall_color=1|9`, and
`n_noise=0..2`; all combinations are supported in every band. Overrides can
remove the default teaching property and must be checked as separate lessons.

Kind: `per_puzzle`. Scope remains a rectangular chamber lattice, a documented
subset of the more general component-based Racket rule. Tests and successful
checks do not change approval or training-admission labels.
