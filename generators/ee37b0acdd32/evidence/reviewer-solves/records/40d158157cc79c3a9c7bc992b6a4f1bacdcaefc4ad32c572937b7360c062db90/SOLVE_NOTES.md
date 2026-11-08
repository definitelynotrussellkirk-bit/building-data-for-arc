# Solve work log

## Earlier exposure

Before this visible-only solve I had not opened the task's generator, Racket rule,
reference solution, private query labels, audit records, or any repair-target source.
I used only the prepared visible examples and my own local checks.

## Revision 1 — component-chain hypothesis

Observation: every input is one 4-connected arrangement of differently colored
regions. Colors 1 and 2 occur as unique endpoint regions. The output keeps the
regions along the chain joining those endpoints, recolors every retained cell 8,
and removes regions attached as side branches.

A cell-level path is too permissive: in training example 1 the two-cell color-9
branch touches the color-3 block at two cells, yet it is removed. Treating each
maximal same-color 4-connected region as one graph node explains this. Build
adjacency between touching regions and retain the shortest component path from
the color-1 node to the color-2 node.

Probe: a local visible-example test initially failed on the untouched template
with `NotImplementedError`, as expected. After implementing the component graph,
I compared the complete output arrays for all three training pairs. Remaining
uncertainty is limited to unseen graphs with multiple equally short component
paths; the visible tasks present a tree-like chain with branches.
