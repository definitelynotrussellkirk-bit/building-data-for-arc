# Solve work log

## Exposure record

Before this blind solve I had read only the packet-wide instructions (`WELCOME.md`,
`RETURN-GUIDE.md`, `ARC-DESIGN.md`, `repo/AGENTS.md`, and the printed assignment).
I had not opened task `47993d3762b9`'s generator, Racket rule, canonical record,
prior notes, reference solutions, private labels, or audit records.

## Revision 1 — harness diagnostic

I ran the prepared `NotImplementedError` placeholder once as a diagnostic probe to
confirm the visible-example checker was active. It errored on all four examples,
as expected. This was not a proposed solution.

## Revision 2 — per-color bounding-box corners

Observation: for every nonzero color, the output erases the original marks and
places that color at the four corners of the smallest axis-aligned rectangle
containing all of its input cells. This explains:

- two diagonally separated cells becoming all four rectangle corners;
- three cells with a redundant/interior edge point becoming four corners;
- four diamond/cross-like cells becoming the enclosing rectangle's corners;
- independent handling of multiple colors in the same grid.

Probe: I manually checked the extrema for each color in all four demonstrations.
For example, train 1 color 8 spans rows 0..2 and columns 0..3, yielding exactly
(0,0), (0,3), (2,0), and (2,3). Color 2 spans rows 0..3 and columns 5..7 and
matches the same rule. The other examples agree.

Implementation: collect coordinates by nonzero color, create a zero grid of the
same shape, and paint the Cartesian product of each color's minimum/maximum row
and column. I preserve input dimensions and avoid mutating the input.

Remaining uncertainty: examples do not show a degenerate one-row or one-column
bounding box, but using the set of min/max coordinates naturally produces two or
one distinct cells in those cases without special casing. The two visible query
outputs are predicted by the same rule.
