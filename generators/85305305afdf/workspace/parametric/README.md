# Parametric family: 85305305afdf

- `finish=canonical` preserves the exact selected ARC program.
- `finish=fill_largest_bbox` executes the canonical terminal-cell shift, then
  finds the unique largest same-color component in that intermediate and fills
  its bounding box with color 9.

The teaching motif alternates isolated movers with three-cell runs. Before Step
A these are separate objects; after Step A they merge into a unique, input-sized
component with a multi-row bounding box. Two demonstrations distinguish the
finite settings. Demo/query counts are independent, and the fourth query is a
substantive 30×30 protected-Racket stress case.
