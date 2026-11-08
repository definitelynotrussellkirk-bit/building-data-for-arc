# Solve work log

## Exposure

Before this solve I had read only packet-level directions and the current assignment. I did not open task `5c577e82a07f`'s generator, Racket rule, reference solution, private labels, notes, or audits.

## Revision 1 — complete rectangle outlines

For each nonzero color, the input contains four cells at the corners of an axis-aligned rectangle. The output preserves those markers and fills every cell along the rectangle's top, bottom, left, and right edges with the same color. Rectangles of height or width two therefore appear solid, which explains the narrow examples without a separate rule.

I first added `test_solution_visible.py`, which loads the visible challenge and failed against the unimplemented template. The implementation groups nonzero cells by color, takes each group's row/column extrema, and paints the perimeter. It does not hard-code grid dimensions, rectangle locations, colors, or thickness.

Probe: `python3 -m unittest -v test_solution_visible.py` from `WORK/solve-blind/` passes all three visible training pairs. Remaining uncertainty is limited to hypothetical overlapping rectangles of different colors; no visible example has a conflict, and the implementation preserves existing nonzero markers at intersections.
