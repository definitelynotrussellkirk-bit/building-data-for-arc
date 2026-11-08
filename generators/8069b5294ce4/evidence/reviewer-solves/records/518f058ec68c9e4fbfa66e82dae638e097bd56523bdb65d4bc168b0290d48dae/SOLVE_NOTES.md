# Solve work log

## Exposure statement

Before this blind solve I read only the packet-level instructions and the visible
examples produced by `python3 review.py blind prepare`. I did not open this task's
generator, Racket rule, reference solution, private labels, notes, audits, or any
other generator source.

## Revision 1 — object-contact graph

The outputs are square matrices with `1` on every diagonal entry and symmetric
`8` entries off the diagonal. I interpreted each nonzero monochrome 4-connected
component as an object and each `8` as a shared-edge contact between two objects.

The examples also contain disconnected distractors. The output size matches the
number of objects in the largest side-connected cluster, not the total number of
objects. Within that cluster, matrix rows/columns follow object reading order:
the lexicographically first occupied cell, i.e. topmost and then leftmost.

Checks against the visible examples by hand:

- Example 0 keeps colors 1, 3, 6, 9 and drops the isolated 7 block. Its contacts
  are 1–6, 3–6, and 3–9, matching the displayed 4×4 matrix in reading order.
- Example 1's seven-object cluster appears in order 2, 3, 1, 7, 5, 4, 6; its six
  shared-edge contacts reproduce every displayed off-diagonal 8.
- Examples 2 and 3 likewise match, while their left-hand distractors are omitted.

I implemented this directly: extract monochrome objects, build their edge-contact
graph, select its largest connected component, sort objects by first cell, and
emit `1` on the diagonal plus `8` for contacts. For an unshown tie between equally
large clusters, the program deterministically prefers more occupied cells and
then the earlier cluster. That tie policy is not established by the examples and
is the main remaining uncertainty.
