# Solve work log

Earlier exposure before this solve: none to this task's rule, generator, notes, reference solution, or private labels. I used only the visible examples emitted by `review.py blind prepare` and `challenge.json`.

## Revision 1 — connected-object packing

Observation: every input consists of several spatially separated nonzero objects. The output preserves each object's colors, orientation, and cropped bounding box, but removes its original location. Objects are arranged left-to-right by increasing number of colored cells, top-aligned, with exactly one all-zero separator column. Example 4 is decisive: the two disconnected color-3 regions become separate objects, so objects are connected components rather than colors.

Implementation hypothesis:

1. Find monochromatic 4-connected nonzero components.
2. Crop each component to its bounding box without rotating or reflecting it.
3. Sort by component cell count; use original top-left position only as a deterministic tie-break because no visible example establishes a semantic tie rule.
4. Top-align the crops in a canvas whose height is the largest crop height and insert one zero column between adjacent crops.

Before implementation I ran a local visible-example test against the starter and confirmed it failed with `NotImplementedError`. After implementation the same test is expected to cover all five labelled pairs. Predicted queries:

- Query 0: `[[3,0,5,0,7,0],[0,0,5,0,7,7],[0,0,5,0,7,0]]`
- Query 1: `[[6,0,7,0,4,4],[0,0,7,0,4,4]]`

Remaining uncertainty: visible examples do not define ordering for equal-area components, whether diagonally touching cells join, or whether differently colored orthogonally touching cells can form one object. I chose standard monochromatic 4-connectivity and stable spatial tie-breaking; those choices do not affect the shown cases.
