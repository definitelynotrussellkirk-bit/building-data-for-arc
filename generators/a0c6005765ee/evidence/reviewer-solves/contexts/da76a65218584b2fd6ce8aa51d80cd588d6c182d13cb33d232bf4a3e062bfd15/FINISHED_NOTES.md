# Blind visible-only solve: a0c6005765ee

I inspected only the preparation tool's public grids and dimensions. I have
not opened any generator, canonical rule, private labels, notes, previous
solutions, or audit evidence before this attempt.

## Revision 1 — frame-side rays

The three visible training inputs are 13x15, 10x13 and 16x10, with outputs of
the same respective sizes. Each has a hollow gray (5) rectangular frame and
orange (7) markers one cell outside its sides. Green (3) is added throughout
each interior row aligned with a left/right marker and each interior column
aligned with a top/bottom marker. The union of these rays is painted; the
frame, markers, background and overall dimensions stay intact.

A filled-interior hypothesis contradicts the remaining interior zero cells.
A horizontal-only hypothesis contradicts the vertical stripes in examples 0
and 2. No failed code revision was needed to identify the visible pattern.

Implementation finds the gray bounds, reads markers adjacent to each side,
and fills the corresponding union of interior rows and columns on a copy.
The query dimensions are 11x14 and 13x11; their output dimensions and correctness
are withheld. My hypotheses predict a row/column union for query 0 and one
vertical interior stripe for query 1, but these are predictions, not labels.

The visible examples contain one gray frame with an empty interior and fixed
colors. Multiple frames, non-adjacent markers and different color roles are
outside the observed support. I will stop if this first implementation matches
all visible demonstrations and executes on both queries.

## Observed check and stopping decision

The first check invocation could not create its attempts directory because the
shared overlay filesystem had no free inodes (Errno 28). It did not score a
solution revision. I copied this working tree to another filesystem, verified
all 55,276 files byte-for-byte, and retried the unchanged code. Revision 1 then
completed with 3/3 visible examples passed. The checker withheld query labels.
I stopped after that successful visible check; I made no code revision and
consulted no reference.
