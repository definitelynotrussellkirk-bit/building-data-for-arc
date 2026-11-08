# Solve work log

This is the fresh post-repair solve bound to final generator SHA
`2b1bfbcfb59638475bc152c8792ba04672d8b400f1689fc78176314f1369c353`.
I had earlier exposure to the task rule during generator review, so this is not a
blind record. After preparation I used only the visible examples and did not
consult the generator, Racket rule, private labels, reference solutions, or the
archived prior solve.

## Revision 1 — count sliding all-1 2 × 2 windows

The output is always a five-cell unary row: a number of leading `1`s followed by
`0`s. In train example 0, the color-1 rectangle at columns 3–4 spans four rows,
so it contains three overlapping 2 × 2 windows and the output has three ones.
Train example 1 has a two-column, three-row target strip, giving two windows.
Train example 2 has no 2 × 2 all-1 window and produces all zeros. Color-2 blocks
and isolated color-1 cells are distractors.

I implemented a complete sliding scan over every 2 × 2 position. By the same
visible rule, query 0 contains a two-column, three-row strip (two windows), and
query 1 contains a two-column, six-row strip (five windows). The overlap cases
are decisive against a connected-component shortcut.
