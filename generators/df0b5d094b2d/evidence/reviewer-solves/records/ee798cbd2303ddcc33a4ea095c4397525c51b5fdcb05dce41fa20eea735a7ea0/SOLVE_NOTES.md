# Solve work log

Earlier exposure before this blind solve: none. I did not inspect the task's generator, canonical rule, reference answers, private labels, audit records, or prior solution explanations.

## Revision 1 — diagonal translation encoded by the 8 corner

Across all three visible training examples, each non-background component is a solid single-color object with one cell replaced by color 8. The 8 is always at a bounding-box corner. The output removes the 8, restores that cell to the object's color, and translates the whole object one cell diagonally in the direction of that corner:

- top-left marker: up and left;
- top-right marker: up and right;
- bottom-left marker: down and left;
- bottom-right marker: down and right.

I checked this object-by-object against every visible pair. For example, the 5x3 color-9 block in training pair 1 has its 8 at bottom-right and moves from rows 2–6 / columns 0–2 to rows 3–7 / columns 1–3. The color-4 block in the same pair has a top-right marker and moves up-right. The other visible objects follow the same rule.

Implementation: find 4-connected non-7 components, identify the unique 8 and the component's ordinary color, infer the marker corner from the component bounding box, clear the canvas to 7, and redraw every component one diagonal cell away with the 8 replaced by its object color. This also handles color 0 as an object color, which appears in the first query.

Remaining uncertainty: the visible examples do not show malformed components, multiple markers, or collisions. The fallback preserves a malformed component in place; the intended generated domain appears to use exactly one corner marker per separated object.
