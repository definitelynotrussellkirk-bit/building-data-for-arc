# Solve work log

## Exposure record

Before this post-repair solve I had already inspected the assigned generator and
canonical rule as part of the required repair, so this is **not blind** and
`earlier-exposure=yes` is required. During this solve I did not reopen the
Racket rule, generator, reference outputs, private query labels, or prior solve
explanations. I used only the newly materialized visible examples.

## Revision 1

The visible examples contain one connected red (`2`) shape and several isolated
single-cell markers in colors `1`, `3`, `4`, and `6`. Outputs discard the input
and contain only cyan (`8`) copies. Comparing the same prototype at different
markers gives the clockwise rotation code:

- `1`: unchanged
- `3`: 90 degrees clockwise
- `4`: 180 degrees
- `6`: 270 degrees clockwise

The prototype is first translated to the top-left of its bounding box. Each
rotated normalized shape is then translated so its top-left cell is the marker
coordinate, clipped to the canvas, and unioned into a fresh zero grid. Repeated
marker colors still produce separate copies; this is visible in the teaching
examples.

I implemented that direct geometric rule. Remaining uncertainty before checking:
none material for the visible examples; edge clipping is inferred from the
fresh-grid stamping convention and guarded explicitly.

## Revision 2

The first check did not evaluate the hypothesis: it raised `ValueError` because
`_normalize` traversed a generator twice, exhausting it while finding the first
minimum. The saved traceback identified this exact data-flow bug. I changed only
that helper to materialize its input once before computing row and column minima;
the geometric rule is unchanged.
