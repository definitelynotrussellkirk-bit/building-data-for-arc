# c3dcd7ae3aaf

Recolor each 4-connected cyan component orange exactly when it is a straight horizontal or vertical triomino. Leave all other cyan components unchanged.

Kind: `per_puzzle`. Current version: `2.0.0`.

The ordinary generator now emits contrastive 8x8–10x10 lessons. Every draw contains horizontal and vertical targets, multiple targets, an unchanged L-triomino, an unchanged straight domino, and both edge and interior targets. Public axes are limited to four facts recoverable from the returned grid: height, width, target count, and distractor count.

Focused regression tests are in `tests/test_generator_c3dcd7ae3aaf.py`.
