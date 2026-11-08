# Solve work log

## Exposure declaration before solving

I had already inspected this task's generator and canonical rule while performing
the required repair, so this is an exposed post-repair solve rather than a blind
solve. During this solve phase I used only the visible examples printed by
`solve prepare`, the challenge files in this directory, my own Python, and the
visible-example checker. I did not reopen the generator, Racket source,
reference solutions, private query labels, or previous solution explanations.

## Revision 1 — row-count compaction inside the two background regions

The visible examples all contain a single straight division between colors 8
and 1, with red cells overlaid on either side. Outputs keep each row's red-cell
count within its own background region while discarding the original horizontal
positions. In color 8, red cells are packed against the region's left edge; in
color 1, they are packed against its right edge. Vertical splits require treating
the two row segments separately, while horizontal splits contain only one
background region in each row.

I implemented a shape-preserving solver that first finds the unique horizontal
or vertical 1/8 split while treating red as a wildcard, reconstructs the clean
background, then counts and compacts red cells independently for every row and
region. The main alternative considered was rigidly translating connected red
objects, but the ragged objects in the visible examples change internal row
offsets, so row-wise counts are the better-supported rule.
