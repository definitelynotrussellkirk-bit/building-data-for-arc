# Solve work log

Earlier rule exposure: **no**. I used only the public `challenge.json`, the dimensions/grids printed by `blind prepare`, and my own scripts over those visible grids.

## Observations and probes

The dominant color forms full separator rows and columns. Removing those lines leaves bands of width/height one or three. The 3×3-by-3×3 intersections are data panels; the thin bands are selectors/labels and remain unchanged.

I wrote a small read-only probe over `challenge.json` to list each 3×3 panel's accent-color coordinates. The output differences revealed two independent uses of color 8:

1. A four-pixel 8 shape is a primary selector. In every training example, a signal-colored panel with the identical four-pixel shape occurs in the selector's panel row, another occurs in its panel column, and the output recolors matching signal panels in the resulting row/column Cartesian rectangle. Distractor panels with the same shape outside that rectangle stay unchanged.
2. A three-pixel horizontal 8 line is a secondary selector. It recolors signal-colored horizontal lines in the same panel column, accepting top/middle/bottom vertical offsets. Similar horizontal lines in other panel columns stay unchanged.

This accounts for every changed and unchanged accent panel in all three demonstrations. In particular, it explains why the line at another column in training example 1 and the top-row line at another column in training example 2 are not painted.

## Revision 1

Implemented separator detection, 3×3 panel extraction, exact accent signatures, primary rectangle completion, and column-scoped horizontal-line propagation. For the primary selector I require the same non-8 signal color to appear with the marker shape on both axes before painting; this avoids choosing an unrelated one-axis distractor.

Remaining uncertainty before checking: the demonstrations contain one signal color per puzzle, so the both-axis color selection rule is inferred from structure rather than contrasted against a visible multi-signal example. The spatial behavior itself is fully contrasted by visible distractors.
