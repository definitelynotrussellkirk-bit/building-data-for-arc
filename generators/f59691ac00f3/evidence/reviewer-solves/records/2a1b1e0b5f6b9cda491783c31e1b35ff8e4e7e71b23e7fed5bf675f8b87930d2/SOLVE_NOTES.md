# Solve work log

## Exposure statement before solving

I had not opened this task's generator, canonical rule, prior solutions, notes, or
private query labels. I had only read the packet-level workflow and the visible
examples produced by `blind prepare`.

## Visible pattern and hypotheses

The non-background first row seeds a narrowing wedge. At depth `r`, only columns
`r .. width-r-1` can be non-background. My first plausible description was to
copy a shifted slice of the top row, but that fails on training example 0: a
constant row of color 5 becomes color 2 on the next row.

The examples instead support a one-step recurrence. Each lower cell takes the
cell immediately up-left, shifts it one column right, and swaps colors 2 and 5;
color 7 stays background. The right edge is clipped by one additional column per
row, so the active interval narrows on both sides. Equivalently, at `(r, c)` the
source is top-row cell `(0, c-r)`, with 2 and 5 swapped when `r` is odd.

Checks against the demonstrations:

- A top row of all 5 alternates 5/2/5/2/5 while narrowing, matching example 0.
- In example 1, the 2 at column 6 propagates to columns 7, 8, 9 as 5, 2, 5;
  interleaved 7 cells remain 7.
- In example 2, each pair `2,2` becomes `5,5` one row down and shifts right;
  the next row swaps back.

A pre-implementation probe imported the template and failed with the expected
`NotImplementedError`, establishing the red state before implementing the rule.
Remaining uncertainty is only whether the hidden generator describes the same
operation recursively or directly from the top row; those formulations are
identical for the visible palette and clipping rule.
