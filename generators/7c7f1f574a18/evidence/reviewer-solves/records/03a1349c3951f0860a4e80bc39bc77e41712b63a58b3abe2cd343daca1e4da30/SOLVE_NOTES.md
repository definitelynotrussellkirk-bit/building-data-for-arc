# Solve work log

## Exposure statement

Before this solve I had read only the packet-level welcome, assignment, return
instructions, and general repository overview. I had not opened task
`7c7f1f574a18`'s generator, Racket rule, reference solution, private query
labels, prior solve notes, or audit records.

## Visible-example observations

Each grid has one dominant background and several separated three-row objects.
The output keeps every object's vertical position and exact binary shape, erases
its old location, recolors it, and places it flush against a horizontal edge.
Input object colors are not semantic: train example 2 uses 1, 6, and 8 for
objects, but the same shape behavior remains.

I first considered position, width, pixel count, and apparent arrow direction.
Those fail as a common explanation: solid 3x3 blocks and the wider pointed
objects both move left, while several widths and counts move right.

The consistent distinction is whether the object is **closed**:

- A solid object is closed.
- A non-solid object is closed when it encloses at least one background cell.
- A shape whose apparent cavity is connected to the exterior through a notch is
  open.

Closed objects move to column 0 and become color 2. Open objects move so their
right edge touches the grid's right edge and become color 3. The row coordinate
and shape orientation do not change.

This explains every visible object, including the otherwise unseen perfect
hollow rectangle in test query 1: it encloses a hole, so it should be treated as
closed and moved left in color 2.

## Probe

I wrote a temporary Python probe against only `solve-blind/challenge.json`:

1. infer the modal background;
2. extract 4-connected non-background components;
3. form each component's bounding-box mask;
4. classify a full mask as closed, otherwise flood empty cells from a one-cell
   exterior frame and detect unreachable empty cells as holes;
5. render closed objects left in 2 and open objects right in 3.

The probe reproduced all three visible training outputs exactly. Component
inspection classified the two query-only cases as expected: the hollow rectangle
is closed, while the notched outlines are open.

## Implementation choice and uncertainty

`solution.py` implements that topology-based rule rather than memorizing widths
or templates. It treats all non-modal colors as object cells, which is necessary
for train example 2. Remaining uncertainty is limited to unseen cases with
objects touching each other or target-edge collisions; neither occurs in the
visible examples and the generated objects appear vertically separated.
