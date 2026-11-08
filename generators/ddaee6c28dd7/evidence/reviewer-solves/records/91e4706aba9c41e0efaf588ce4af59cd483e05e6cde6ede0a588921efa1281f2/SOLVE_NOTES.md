# Solve work log

## Exposure before solving

I read the packet's generic `WELCOME.md`, the generated assignment, and an excerpt
of the generic `ARC-DESIGN.md` before preparation. I did **not** open task
`ddaee6c28dd7`'s generator, canonical rule, reference solution, private labels,
prior solve notes, or audit records.

## Revision 1 — widest-object hypothesis

The demonstrations contain several separated monochrome objects. Cropping each
object to its bounding box gives widths:

- example 0: 6, 3, 5, **7**, 2; the width-7 color-5 object is the output;
- example 1: 5, 5, **6**; the width-6 color-6 object is the output;
- example 2: 2, 5, **6**; the width-6 color-7 object is the output.

The output preserves the selected object's mask inside its tight bounding box,
changes every selected cell to color 8, and leaves background cells 0. This is
more consistent than early alternatives based on area, rectangle status, or
perimeter: those alternatives fail at least one visible example.

I implemented same-color 4-connected components so disconnected objects of the
same color are not accidentally merged. The visible examples have a unique
widest object; tie behavior remains unproven. The predictions are:

- query 0: select the color-9 hollow 4×5 rectangle;
- query 1: select the color-1 irregular 4×7 object.

A train-only regression script first failed on the untouched
`NotImplementedError`, then passed after this implementation. No reference data
was consulted.
