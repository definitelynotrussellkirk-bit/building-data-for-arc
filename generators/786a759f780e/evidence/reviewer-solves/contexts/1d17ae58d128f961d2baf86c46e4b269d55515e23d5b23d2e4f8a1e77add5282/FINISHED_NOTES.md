# Solve work log

## Exposure declaration before revision 1

This is an exposed post-repair solve. Before `prepare` I had already inspected the assigned generator and canonical Racket rule while repairing them, so earlier rule exposure is **yes**. During this solve I used only `solve/challenge.json`, this Python file, and visible check feedback; I did not reopen the generator, Racket source, canonical ledger, private labels, or earlier solution explanations.

## Revision 1 — component crops ordered by a three-key statistic

Visible evidence suggested that every 4-connected nonzero region is one object even when its colors mix. The output preserves each object's tight crop and lays crops left-to-right with one zero column between them, top-aligned.

The five training pairs separate the ordering keys:

- The 0/1/2-hole examples put fewer enclosed zero regions first even when area would prefer another order.
- The all-one-hole example has two 3x3 rings followed by a 4x4 ring, showing increasing painted area rather than decreasing area.
- The equal-size 3x3 rings appear in increasing first/primary color, showing the final deterministic tie-break.
- Mixed-color boundary cells stay attached to their nonzero component and are preserved in its crop, ruling out per-color component extraction.

I implemented: scan row-major for 4-connected nonzero components; remember the first cell's color; count enclosed 4-connected zero regions inside each bounding box; sort by `(hole_count, painted_area, first_color)`; then pack nonzero crop cells horizontally with one black separator. Main remaining uncertainty before checking was whether mixed colors affected hole solidity or the tie color, but the visible mixed examples support treating every nonzero cell as solid and using the row-major seed color.
