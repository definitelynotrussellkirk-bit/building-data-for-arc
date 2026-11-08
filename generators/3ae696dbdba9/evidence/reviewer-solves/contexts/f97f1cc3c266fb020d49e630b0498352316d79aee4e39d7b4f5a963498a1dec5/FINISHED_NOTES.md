# Solve work log

## Exposure record

I had not opened this task's generator, Racket rule, notes, reference solution,
private labels, or audit evidence.  I used only the visible examples in
`challenge.json` / `README.md` and my own local checks.

## Hypothesis development

The first tempting description was “fill each coloured object's bounding
rectangle.”  I rejected that because the colour-6 T shape in train example 1
has a 3×3 bounding box but remains unchanged.

A more precise invariant fits every changed and unchanged object: fill a zero
when two cells of the same nonzero colour bracket it in the same row or in the
same column.  Equivalently, for each colour, close the gaps between its first
and last occurrence on each row and column.  Examples supporting this include:

- the hollow colour-4 3×3 ring, whose centre is bracketed horizontally and
  vertically;
- the colour-2 C-like 4×3 object, whose empty right-hand columns are bracketed
  vertically by its top and bottom bars;
- the colour-6 T, whose occupied row/column runs already have no gaps;
- the staircase-shaped colour-3 query object, which has contiguous runs and
  therefore should remain unchanged.

The implementation uses the original input for both horizontal and vertical
bracket detection.  This makes the operation simultaneous and avoids allowing
a newly filled cell to create an unsupported second wave.  Existing nonzero
cells are never overwritten.

## Expected query behavior

For query 0, fill the centre of the colour-5 ring and the two-by-two interior
of the colour-8 C-like object; leave the colour-3 staircase unchanged.  Query 1
is the shifted analogue of train example 0, so it receives the same two gap
fills.

## Remaining uncertainty

The visible examples do not distinguish simultaneous one-pass filling from an
iterated closure in every imaginable arrangement.  The simultaneous reading is
the smallest rule directly supported by the examples and avoids accidental
propagation across unrelated geometry.

## Revision after local visible check

The first implementation grouped all occurrences by colour.  Train example 0
exposed a concrete flaw: its two disconnected colour-2 objects share a column,
so that implementation incorrectly painted the blank rows between them.  I
refined the rule to act independently on each 4-connected monochrome object.
This preserves the same within-object gap filling while preventing unrelated
same-colour objects from being joined.
