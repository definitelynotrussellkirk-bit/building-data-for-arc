# Solve work log

## Exposure boundary

This is **not a blind solve**. Before `solve prepare`, I had already inspected and
executed the canonical Racket rule while repairing the assigned generator. I
therefore record earlier rule exposure as `yes`. During this prepared solve I
kept the Racket rule, generator implementation, reference solutions, private
query labels, and prior solution notes closed; I used only `challenge.json`,
`README.md`, and my own Python probes.

## Visible hypothesis

Across all three demonstrations, each 30x30 input contains sparse distractor
noise plus conspicuous solid monochromatic rectangles. The rectangles occur in
horizontal groups of three. The output has one row per spatial group, ordered
top-to-bottom, and records the rectangle colors in left-to-right order. Rectangle
area and dimensions vary, so size is not encoded in the output.

Examples supporting this reading:

- Train 0 has upper rectangles colored `3,4,1` and lower rectangles `3,9,7`.
- Train 1 has three spatial rows colored `1,6,1`, `9,5,8`, and `6,9,5`.
- Train 2 has four spatial rows matching its four output rows.

## Probe and implementation

I wrote a visible-data-only component probe that listed each same-color
4-connected component's size, bounding box, density, and center. Every intended
rectangle exactly fills a bounding box with both dimensions at least three. The
sparse distractors either fail that solid-box test or have a dimension below
three. One visible query includes a 3x3 rectangle, so the minimum cannot be set
above nine cells.

`solution.py` therefore:

1. finds nonzero same-color 4-connected components;
2. retains components that exactly fill a bounding box at least 3x3;
3. clusters their vertical centers into rows (within-row center variation is at
   most 1.5 cells in the demonstrations, versus much larger between-row gaps);
4. retains three-rectangle rows and emits their colors left-to-right, with rows
   ordered top-to-bottom.

The `len(group) == 3` constraint follows every demonstrated output width and
also discards a hypothetical isolated solid noise block. Remaining uncertainty
is limited to unseen inputs containing a solid 3x3 distractor adjacent to a real
row; no visible example exhibits that ambiguity.
