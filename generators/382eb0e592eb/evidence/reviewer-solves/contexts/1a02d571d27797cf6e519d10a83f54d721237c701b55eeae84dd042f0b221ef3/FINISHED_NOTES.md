# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before preparation I had already inspected the selected rule while repairing the generator, so earlier rule exposure is **yes**. During this solve I did not reopen the rule, generator, reference solutions, private labels, or earlier solution explanations; I used only the visible examples printed by preparation.

## Revision 1

Visible-example hypothesis: every adjacent pair of equal, nonzero cells in a row paints the same two positions in the row immediately below. Trigger detection must use the original input.

Evidence from the visible examples:

- Train 0 has two isolated horizontal pairs; each becomes a 2×2 block.
- Train 1 contains a length-three run of color 4. All three cells appear below, which means both overlapping adjacent windows fire. The middle target was color 5 and is overwritten, so the target need not be blank.
- The vertical color-5 cells in train 1 do not trigger anything.
- The color-5 pair on the bottom row in train 1 stays inert because no row exists below it.
- Train 2 confirms that separate pairs on successive rows are detected from the original input rather than recursively from newly written cells.

Implementation: copy the grid, scan all non-bottom rows and adjacent columns in the original grid, and write both target cells for every equal nonzero pair. Remaining uncertainty before checking: none among the visible cases; the masked queries are still withheld by policy.
