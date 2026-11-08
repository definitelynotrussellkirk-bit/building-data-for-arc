# Solve work log

## Prior state

I had already inspected this task's generator and selected Racket authority during the repair lane, so this is **not blind**. During this solve phase I consulted only the prepared visible challenge and did not reopen the generator, rule, references, or private labels.

## Revision 1 — framed motif expanded by rotation codes

Visible observations:

- Every input contains one hollow color-1 frame. Its complete interior is an `n × n` colored motif with zero background.
- A separate dense rectangle contains values 2, 3, 4, and 5.
- Output dimensions equal `(code rows × n) × (code columns × n)`.
- Splitting each visible output into `n × n` tiles shows that each code cell selects a rotation of the framed motif: `2 → 0°`, `3 → 90° clockwise`, `4 → 180°`, and `5 → 270° clockwise`.
- The motif color is preserved rather than replaced by the code value.

Implementation: locate the color-1 bounding box, crop its interior, locate the outside 2..5 bounding box, rotate the motif `code - 2` times clockwise, and paste each tile into the corresponding output block. This is position- and size-generic for the visible family.

Remaining uncertainty: the examples contain exactly one frame, one source color, and a fully filled code rectangle; the solution deliberately assumes those visible invariants.
