# Initial blind solve

## Information boundary

I ran `python3 review.py blind prepare` and read only this episode's
`README.md` and `challenge.json`. I have not opened a generator, canonical
rule, reference solution, prior solution notes, audits, or private labels.
There was no earlier rule exposure. The observations below come only from
the three public input/output examples and two public query inputs.

## Inferred transformation

Each nonzero object is an adjacent, same-color pair, either horizontal or
vertical. Every pair becomes a filled 2-by-2 square of its original color,
anchored at the pair's top-left cell. A horizontal pair gets an identical
pair immediately below it; a vertical pair gets one immediately to its
right. The grid dimensions, original colored cells, and other background
cells stay the same.

This direction is consistent across all colors and placements. The first
example expands the vertical 1 and 7 pairs to the right and the horizontal
4 pair downward. The second does the same for vertical 3 and 5 pairs and
horizontal 7. The third expands horizontal 5 and 8 pairs downward and the
vertical 1 pair rightward. Thus colors identify objects but do not select
different directions. Expanding upward/leftward, extending pairs along
their existing axes, or moving the originals would contradict the shown
outputs.

## Candidate 1

`solution.py` copies the grid, finds same-color four-connected components
in the original input, and expands each two-cell component perpendicular
to its orientation. Reading components from the original input prevents
newly painted pixels from triggering additional expansions. Components
are found separately even if a future input reuses a color.

All observed components have two cells and every expansion fits within
the grid. The code leaves other component sizes alone and bounds-checks
painted cells defensively; those choices are not supported or tested by
the visible lesson. No visible example or query contains overlapping
target squares, so overlap resolution is also unestablished.

## Public query predictions

Coordinates are zero-based (row, column). Original pixels are retained.

- Query 0: add color 5 at (0, 7) and (1, 7); color 6 at (1, 3)
  and (2, 3); color 3 at (6, 7) and (6, 8).
- Query 1: add color 1 at (2, 3) and (3, 3); color 7 at (4, 6)
  and (4, 7); color 2 at (5, 0) and (5, 1); color 5 at (7, 6)
  and (8, 6).

## Check history and stopping criterion

This is the first and only candidate so far. No failed candidate has
been removed. I am submitting it to the required blind check with intent
`solve` to compare against all visible outputs and exercise query
execution. The check's saved feedback is the authoritative record of
the result. If it passes, the rule accounts for all nine demonstrated
objects and the queries require no further geometric extrapolation, so
I will finish without consulting withheld answers.
