# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, reference solution, private labels,
or prior notes for task `aea4d55345a1`. I used only `solve-blind/challenge.json`
and the public solve instructions. Earlier rule exposure: no.

## Revision 1 — next frame of a film strip

The input is divided by full-width rows of color 5 into four equal panels. The
output in every training pair is the fifth panel of the same sequence.

Two sequence mechanisms are visible:

1. A compact multicolor foreground object translates by a constant horizontal
   displacement. Training examples move `[3,3,9]` by one column and
   `[8,9,8,9]` by two columns.
2. A color front advances one column per panel, replacing an old foreground
   color while preserving holes and an unrelated static pattern.

I implemented both mechanisms rather than hard-coding the two test outputs.
The program first recognizes single-column, single-color-pair changes with a
constant column step. Otherwise it checks that the non-background foreground
shape is unchanged up to a constant translation and advances it once more.

Expected test behavior from the visible inputs:

- Test 1 recolors the next (fifth) column from 9 to 8, preserving zeros.
- Test 2 shifts the `[2,8,2,8]` row two columns right, from columns 6–9 to 8–11.

Remaining uncertainty: the separator detector assumes the solid nonzero rows
are separators, as they are in all visible examples. The implementation rejects
unsupported sequences instead of guessing.
