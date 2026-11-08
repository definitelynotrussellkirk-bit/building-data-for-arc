# Solve work log

This is a human-authored work log. I did not consult the Racket source, generator implementation, reference solution, private query labels, or prior solution artifacts during this solve phase. I **had earlier rule exposure** while reviewing the assigned generator before `solve_episode.py prepare`; the final declaration therefore uses `earlier-exposure=yes` even though the observations below were checked against `challenge.json` alone.

## Revision 1 — exactly-one-border connected objects

Visible-example observations:

- Training pair 1 keeps the vertical color-5 object on the top edge. It erases the color-3 object at the top-left corner (two edges) and the interior color-1 object.
- Training pair 2 keeps the color-2 object on the right edge. It erases the color-8 object at the top-right corner and the interior color-6 object.
- Training pair 3 keeps color 2 on the top edge, color 6 on the left edge, and color 3 on the bottom edge. It erases the top-left color-9 object, the bottom-right color-8 object, and interior color 4.

Hypothesis: split nonzero cells into same-color, four-connected objects. For each object, collect which of the four outer borders contain at least one of its cells. Copy the object to an otherwise-zero output exactly when that set has cardinality one.

Implementation choice: detect components directly rather than relying on one object per color. This handles repeated colors in disconnected objects without merging them. Border contact is collected from actual cells, which is equivalent to checking the component bounding box here but is less indirect.

Local visible-demo probe: executed `solve()` on all three training inputs and compared each result to its visible output. All three matched exactly. No alternate program revision was needed.

Remaining uncertainty before the hidden check: none about the transformation shown by the demonstrations; the only procedural caveat is the declared earlier exposure.
