# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, prior solution notes, or audit evidence. I used only the visible
examples printed by `python3 review.py blind prepare` and the public
`challenge.json` generated from them.

## Revision 1 — center each horizontal run

Across all three visible training examples, every nonzero object is a one-row
horizontal run of odd length 1, 3, or 5. The output keeps the same canvas and
replaces each run by exactly one cell of the same color at the run's horizontal
center. A singleton is therefore unchanged.

Examples supporting the hypothesis:

- Train 0: row 0 color 7 spans columns 0–2 and becomes column 1; row 2 color 2
  spans columns 2–6 and becomes column 4.
- Train 1: row 5 color 4 spans columns 0–4 and becomes column 2; the singleton
  color 6 remains at row 0, column 4.
- Train 2: row 0 color 7 spans columns 6–8 and becomes column 7; row 2 color 5
  spans columns 4–8 and becomes column 6.

Implementation scans each row for maximal same-color nonzero runs and writes the
same color at `(start + end) // 2` in an otherwise zero output grid. This also
keeps adjacent runs of different colors distinct.

The visible data contain no even-length runs, vertical bars, multi-row objects,
or same-color runs touching vertically. I therefore did not invent behavior for
those unsupported cases beyond the natural row-wise interpretation; an even run
would select the left of its two central cells due to integer division.
