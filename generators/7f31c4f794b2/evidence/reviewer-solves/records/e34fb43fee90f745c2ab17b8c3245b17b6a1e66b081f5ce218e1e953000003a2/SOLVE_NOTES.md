# Blind solve: 7f31c4f794b2

## Exposure and evidence
Only `solve-blind/challenge.json` was read. No generator, rule, task notes,
prior solution, audit or private label was consulted. Earlier exposure: no.

## Visible-example exploration
I enumerated same-color orthogonally connected components and printed their
sizes, bounding boxes, normalized shapes and changed cells. Every changed
component becomes 7, without changing its footprint.

Initial ideas considered and rejected from the visible examples: selecting
largest components (works for the first example but not the second), selecting
unmatched or asymmetric shapes (the same normalized L and T shapes change in
one example but not another), and selecting components joined to other colors
(does not explain the isolated changes). These were exploratory hypotheses,
not submitted solution revisions; no failure was manufactured.

The common feature is boundary contact. In example 1 the changed zigzag touches
the left edge and the changed L touches the bottom. In example 2 the changed
triomino touches the top and the changed T touches the right. In example 3 the
changed zigzag touches the right and the changed triomino touches the bottom.
All unchanged monochromatic components are interior. Color-sensitive connectivity
is necessary because some differently colored objects touch orthogonally.

## Revision 1
Use 4-connected monochromatic nonzero components. Recolor the entire component
7 exactly when any of its cells touches any grid edge. Preserve everything else.
Check all three visible examples and submit one genuine solve attempt. Hidden
query correctness is unknown; the official checker withholds it.
