# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private labels,
prior solution notes, or any audit evidence. I only read the public challenge produced
by `review.py blind prepare` and the packet workflow documents.

## Revision 1 — identify the 3×5 spanning color and crop its window

### Observations

Every input contains four nonzero colors. Exactly one color spans a bounding box of
3 rows by 5 columns:

- example 0: color 8 spans rows 0–2 and columns 0–4;
- example 1: color 4 spans rows 2–4 and columns 3–7;
- example 2: color 9 spans rows 6–8 and columns 5–9;
- example 3: color 7 spans rows 5–7 and columns 3–7.

The output is the literal 3×5 input crop at that window, not a rendering of only the
selected color. This explains the two color-6 cells retained in example 1 and the
three color-7 cells retained in example 2. Cells from an object extending outside
the selected rectangle are clipped by the crop.

Alternative hypotheses rejected from the visible data:

- choose the largest color by cell count: example 2 would choose color 7, not color 9;
- choose the largest bounding box: example 2 would choose color 4 (4×5);
- extract and normalize the selected shape alone: examples 1 and 2 retain intruding
  cells of other colors.

### Program

For each nonzero color, compute its bounding rectangle. Select the unique color whose
rectangle is exactly 3×5, then return the corresponding slice of the original grid.
Raise a descriptive error if the visible contract is not unique rather than silently
selecting an arbitrary candidate.

### Predicted queries

Query 0 selects color 3 at rows 0–2, columns 4–8.
Query 1 selects color 3 at rows 6–8, columns 4–8; the crop retains the color-4 cell
at its top-right corner and excludes the adjacent color-4 cell outside column 8.

Remaining uncertainty: the hidden rule could describe the target dimensions more
abstractly, but all four demonstrations uniquely support the exact 3×5 crop contract.
