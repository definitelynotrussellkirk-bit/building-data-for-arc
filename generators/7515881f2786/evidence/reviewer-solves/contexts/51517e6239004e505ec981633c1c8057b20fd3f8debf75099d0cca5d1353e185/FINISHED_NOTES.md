# Solve work log

## Exposure declaration before solving

I had not opened task 7515881f2786's generator, Racket rule, reference solution,
private labels, audit evidence, or any repair-target generator. I used only the
visible examples printed by `python3 review.py blind prepare` and the generated
visible-only files in this directory.

## Revision 1 — aligned original-marker spans

Hypothesis: for every row containing at least two original azure (8) markers,
fill the inclusive horizontal span from its leftmost to rightmost marker. For
every column containing at least two original markers, fill the inclusive
vertical span from its topmost to bottommost marker. Preserve all isolated
markers. Compute both sets of spans from the *original* grid, not iteratively.

Evidence from the visible examples:

- Example 0 has four corners at rows 6/8 and columns 0/4, so the four spans make
  the shown rectangular perimeter. The isolated marker at (4,8) is unchanged.
- Example 1 fills row 5 from columns 3 through 8 and column 3 from rows 5 through
  9. It does not extend column 7 after row 5 is filled, which rules out iterative
  propagation from newly created cells.
- Example 2 fills row 1 from columns 0 through 9 and column 6 from rows 1 through
  5; the other three markers remain isolated.
- Example 3 fills row 1 from columns 0 through 7 and column 2 from rows 1 through
  8 while retaining off-line markers.

Predicted query behavior:

- Query 0: fill row 3 from columns 1..6 and column 5 from rows 1..8; retain the
  isolated marker at (6,7).
- Query 1: the four markers at rows 2/5 and columns 2/5 form a rectangular
  perimeter; retain the isolated markers at (7,1) and (11,4).

Remaining uncertainty: all visible examples use background 0 and marker color 8.
The implementation groups spans by nonzero color, which preserves the inferred
single-color behavior while avoiding accidental connection of different colors.
