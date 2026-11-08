# Solve work log

I began with no earlier exposure to this task's generator, rule, notes, solutions, or audit evidence. I used only the visible examples printed by `python3 review.py blind prepare`.

## Revision 1

Hypothesis: the non-blue three-cell object is a distractor/landmark. Treat every 4-connected blue (`2`) component separately. If a component is a perfectly straight horizontal or vertical segment, recolor its two extreme cells orange (`8`); a length-two segment therefore becomes entirely orange. Leave bent/L-shaped blue components unchanged.

Evidence from the visible examples:

- Every long straight component changes only at its two ends.
- Every two-cell straight component changes both cells.
- Every four-cell L-shaped component remains blue.
- This behavior is unchanged whether the separate three-cell colored object is straight or L-shaped, so I did not use its shape as a selector.

Implementation probe: enumerate 4-connected blue components, test whether all cells share one row or one column, and recolor the extrema. Remaining uncertainty is limited to unseen singleton blue components; the implementation treats the single cell as both endpoints and recolors it orange.
