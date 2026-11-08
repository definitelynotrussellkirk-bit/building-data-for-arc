# e42b0a4cc753

A 6..10 × 7..12 grid has a complete color-8 outer border and an otherwise-zero interior containing 2..5 singleton seeds with pairwise-distinct colors (excluding 0 and 8). Each blank interior cell is filled with the color of its nearest seed under Manhattan distance. If multiple seeds are equally near, the seed first in row-major reading order wins. The wall and original seed cells are preserved.

The version 4.0.0 generator pins selected authority `RULE_HASH = f23844d6433c`. Its exact public controls are `grid_h`, `grid_w`, and `n_seeds`; every supported combination is lawful and observable from returned pixels. Every seed must uniquely own at least one initially blank cell.

Default generation uses a three-slot teaching cycle: a reading-order/lower-color tie discriminator, a consequential third seed, and a Manhattan/Euclidean discriminator. Because `EXAMPLES_NEEDED = 3`, every consecutive three-example lesson contains all three roles. Explicit overrides remain exact and lawful but bypass these pedagogical role guarantees.

Kind: `per_puzzle`. Version: `4.0.0`.
