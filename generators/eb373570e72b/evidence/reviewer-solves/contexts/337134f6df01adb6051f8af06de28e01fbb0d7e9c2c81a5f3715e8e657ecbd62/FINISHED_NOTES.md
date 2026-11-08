# Solve work log

I had no earlier exposure to task `eb373570e72b`. I did not inspect its generator,
canonical rule, private labels, prior solution notes, or any repair target before this
solve. This is a human work log based only on the public challenge.

## Revision 1 — component activation and three-row diagonal flattening

### Observations

- Every color-1 component loses its cells above the bottom row and leaves a horizontal
  trace derived from its lowest three input rows.
- A simple vertical component contributes three consecutive bottom cells: mapping an
  input cell `(r, c)` in the lowest three rows to `(H-1, c + H-1-r)` explains the
  traces at columns 4, 5, 7, 14–15, and the clipped trace at the right edge.
- Some color-2 components remain vertical. The color-2 components that flatten are
  exactly those horizontally enclosed by two color-1 components with the same top
  row. This distinguishes all three demonstrations: the equal-top color-1 bookends
  activate the interior color-2 posts in examples 0 and 1, while the unequal-top
  color-1 posts in example 2 activate none.
- A standing color-2 post leaves one zero column immediately to its left. Thus the
  color-1 trace at column 7 in example 2 is truncated to its base cell before the
  standing post at column 9.
- Moving components are resolved from right to left. If a projected component would
  overlap an already placed moving component, shifting it left preserves its trace.
  This explains the otherwise missing color-2 cell at column 11 in example 1.

### Probes

I used a local Python script over `challenge.json` to list 4-connected components,
their colors, bounding boxes, and sizes. I then tested the above transformation against
all three visible training pairs. The candidate reproduced every visible output exactly
before I wrote `solution.py`.

### Alternatives considered

I considered ordinary clockwise rotation, simple rightward dilation, diagonal gravity,
and a domino-chain interpretation. Each failed at least one visible pair, especially the
color-2 gap at column 11 in example 1 or the standing posts in example 2. The selected
rule is the smallest explicit component rule I found that covers all visible evidence.

### Remaining uncertainty

The public examples do not prove that three rows, equal top coordinates, and the
one-column barrier clearance are the unique intended abstractions. The query predictions
therefore remain uncertain even though the three demonstrations are matched exactly.
