# Fresh solve notes

This is a human-readable work log, not a token-level model trace.

## Visible-example observations

- Every output is exactly two rows shorter than its input and keeps the same width.
- In each input, rows 0 and 1 contain aligned nonzero cells. Treating each column as an ordered pair `row0 color → row1 color` explains every changed body color.
- Training example 1 gives `7→3`, `2→6`, `4→5`; removing the first two rows and making those substitutions reproduces the output.
- Training example 2 is the stronger probe because its key is scattered across columns 3, 6, 7 and 8. The same column-wise rule gives `4→2`, `2→4`, `8→1`, `7→5`, matching all visible output cells.
- Training example 3 contains overlap/swap structure: `6→1`, `1→6`, `2→5`. The output shows one simultaneous pass, not repeated/cascading replacement: body color `6` becomes `1`, not then `6` again.

## Hypothesis

Build a map from every nonzero entry in row 0 to the entry directly beneath it in row 1. Drop the first two rows. Replace each remaining cell once using that map; leave zero or any unkeyed value unchanged.

## Query predictions before running code

- Query 1 key: `3→8`, `8→9`. The 7-row body should retain geometry while all 3s become 8s and all 8s become 9s.
- Query 2 key: `4→2`, `2→3`, `8→9`. The 7-row body should map those colors simultaneously.

## Implementation and probe

Implemented the direct one-pass map in `solution.py`. No alternate implementation or failed revision was needed because all three demonstrations independently support the same rule and the scattered/overlapping examples distinguish the main shortcuts.
