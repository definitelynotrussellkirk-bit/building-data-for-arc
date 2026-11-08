# Solve work log

This is a human-authored work log. I had already inspected this task's generator
and rule during the generator-review phase, so this is **not** a blind solve.
After `prepare`, I consulted only `solve/challenge.json` while writing this
revision; I did not reopen the Racket authority, generator, reference solution,
private labels, or the earlier solve artifacts retained under `checks/`.

## Visible-example observations

- Each nonzero color region is handled as a same-color **4-connected** object.
- The output replaces each object's occupied cells by the full rectangle between
  that object's minimum and maximum row and column.
- Objects sharing a color remain separate. Training example 2 has a color-2
  singleton diagonally separated from the larger color-2 object; the singleton
  stays one cell while the larger object's 2x2 box is completed.
- Training example 3 confirms the same rule on two distant color-1 objects and
  on a dense 4x4 color-4 object containing interior gaps.
- Background remains 0, and output construction is independent for each object.

## Revision 1 hypothesis

Flood-fill every nonzero same-color 4-component, compute its tight bounding box,
and paint that entire box with the component color on a fresh zero grid. This
should reproduce all three visible outputs and handle the two masked inputs.
