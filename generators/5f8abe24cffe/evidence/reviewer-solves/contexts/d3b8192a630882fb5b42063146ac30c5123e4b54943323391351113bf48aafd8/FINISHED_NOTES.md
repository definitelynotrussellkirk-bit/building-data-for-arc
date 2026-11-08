# Blind solve: 5f8abe24cffe

Earlier exposure: no. I have opened only the assigned public challenge and its
starter solution. No generator, Racket source, private labels, prior solutions,
notes, or audit records have been consulted.

## Initial hypothesis and visible probe

The three blue rectangular frames enclose small colored arrays. Ignore the
frames and remove all-zero exterior rows and columns of each interior. A pair
of arrays demonstrates a square-grid isometry. Apply that same isometry to the
remaining array and return the resulting array without a frame.

I enumerated the eight rotations/reflections on the public challenge only.
For train 0 (14 x 12 input, 4 x 3 output), panel 0 maps to panel 1 by a clockwise
quarter turn. The same transform maps the third panel to the displayed output.
For train 1 (20 x 6 input, 2 x 4 output) and train 2 (13 x 12 input, 2 x 2 output),
the first-to-second relation is transpose; transposing the remaining panel
matches both displayed outputs exactly.

A real ambiguity appears in train 0: the demonstrator's repeated columns make
a second reflected transform fit the first two panels. It gives a different
answer for the third panel. The visible output selects the unreflected quarter
turn. I therefore prefer pure rotations to reflected transforms when the
example pair alone is symmetric. This is a convention supported by the one
ambiguous visible lesson, not a proof for every possible task instance.

The public queries have unique identified transforms in this enumeration:
transpose for query 0 and identity for query 1. Their output dimensions and
correctness are unknown to me; I have not opened private labels. The candidate
arrays were computed only from these input panels.

## Revision 1

Implemented connected-component frame extraction, foreground bounding-box
cropping, and the eight isometries. Reading order determines the direction of
the relation between the matched pair. No failed solution revision was
manufactured. The next command checks only the displayed examples and execution.

Revision 1 completed successfully: 3/3 visible examples matched. Masked-query
correctness remains withheld. I stopped because the two public query inputs
have unambiguous relations under the supported transform family, and the
visible checker finds no mismatch. The tie-precedence limitation remains.
