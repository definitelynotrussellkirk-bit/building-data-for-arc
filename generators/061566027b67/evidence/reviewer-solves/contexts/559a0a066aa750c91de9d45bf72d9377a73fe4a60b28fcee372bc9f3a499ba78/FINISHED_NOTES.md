# Solve work log

## Exposure declaration before solving

I had not opened task `061566027b67`'s generator, Racket rule, reference solutions,
private labels, audit records, or any earlier explanation. I used only
`solve-blind/challenge.json` and my own local reasoning/code.

## Revision 1 — isolate the planted solid rectangle

### Observations

All three demonstrations are 16×16 fields of sparse multicolor noise containing
one conspicuously large, solid, axis-aligned rectangle of a single nonzero color.
The output preserves exactly that rectangle in place and changes every other cell
to background 0.

The same-colored noise can touch or extend beyond the intended rectangle, so a
connected-component bounding box is unsafe:

- Example 1 preserves a 3×3 block of 7 at rows 11–13, columns 0–2, while an extra
  7 directly below at row 14, column 2 is discarded.
- Example 2 preserves a 6×2 block of 3 at rows 5–10, columns 2–3, while an extra
  3 at row 11, column 3 is discarded.
- Example 3 preserves a 3×4 block of 4 at rows 5–7, columns 7–10; nearby 4s are
  noise and are discarded.

### Hypothesis

Find the maximum-area all-equal, nonzero, axis-aligned rectangle with both height
and width at least 2. Return an all-zero grid except for that rectangle. If no
2D rectangle exists, fall back to the maximum-area same-color rectangle without
the dimension restriction so the function remains total.

### Implementation/probe

I implemented an exhaustive row-pair search. For each nonzero color and each
`top..bottom` row interval, it marks columns whose entire vertical segment equals
that color, then scans contiguous marked runs. This directly searches solid
rectangles and is insensitive to attached same-color protrusions.

Remaining uncertainty: demonstrations do not specify tie-breaking between equal
maximum rectangles. The generated examples appear to have a unique dominant
rectangle; the implementation uses deterministic first-in-row-major order for a
tie.
