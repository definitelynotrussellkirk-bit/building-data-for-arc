# Solve work log

## Exposure declaration

I had already inspected this task's rule and generator while performing the assigned repair, so earlier rule exposure is **yes**. During this freshly prepared solve episode I used only the visible examples/challenge and my own Python; I did not consult the Racket source, generator implementation, reference solutions, private query labels, or the archived prior solve.

## Visible observations

- Example 0 has four gray-5-bounded regions. Each contains one seed from 1..4, and every zero connected to that seed becomes its color.
- Example 1 rules out a rectangular/full-line-only interpretation: color 6 forms a stepped/partial divider, yet the output fills the full four-neighbor connected regions.
- Example 2 has two large irregular regions and shows that seed position does not matter; all connected zeros on the same side receive the seed color.
- Wall color is not fixed: examples use 5 and 6, and a query uses 7. The invariant appears to be that colors other than 0 and the active seed are barriers.

## Hypothesis and implementation

For every cell whose original color is 1, 2, 3, or 4, run a four-neighbor flood through original cells equal to 0 or that seed color. Copy the grid and recolor only visited zeros. Read traversability from the original grid so an earlier fill cannot alter a later flood.

The Python implementation enumerates all seed cells, performs BFS for each, and preserves every nonzero input cell.

## Alternatives rejected from visible evidence

- Filling rectangles between complete wall rows/columns fails the stepped and partial wall geometry in example 1.
- Treating only color 5 as a wall fails examples/query grids with wall colors 6 and 7.
- Nearest-seed or geometric Voronoi assignment is unnecessary and would cross explicit barriers.

## Remaining uncertainty

The visible examples have one seed per connected chamber, so they do not specify conflict resolution for overlapping floods of different colors. The proposed rule matches all three demonstrations without needing such a tie-break.
