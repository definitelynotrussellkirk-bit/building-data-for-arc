# Solve work log

## Prior exposure declaration

I had already inspected this task family while reviewing and repairing its generator, so this is not a blind solve. After `solve_episode.py prepare` created this final-source episode, I did **not** consult the generator, Racket rule, reference solutions, private labels, or the prior solve preserved elsewhere in the packet. I used only this episode's `solve/challenge.json`, my own Python, and the permitted visible-example checker.

## Visible-example analysis

In each training input, most nonzero colors occur exactly three times. The three positions for each such color use exactly two row coordinates and two column coordinates, so they are three corners of an axis-aligned rectangle. The output adds the same color at the unique missing Cartesian-product corner and preserves all original cells.

A color that occurs once is a distractor and remains unchanged. Color identity is not the rule: the third demonstration uses color 9 as a three-cell active rectangle while color 4 is the singleton. The consistent discriminator is therefore occurrence count plus rectangle geometry.

## Implementation

The solver copies the grid, groups nonzero coordinates by color, and only considers groups of exactly three cells. It requires exactly two unique rows and two unique columns, computes the four candidate corners, and fills the unique absent corner when it is background. Every other group and cell is preserved.

The demonstrations supported this implementation directly, so I made one solve revision and submitted it to the visible checker without manufacturing a failed alternative.
