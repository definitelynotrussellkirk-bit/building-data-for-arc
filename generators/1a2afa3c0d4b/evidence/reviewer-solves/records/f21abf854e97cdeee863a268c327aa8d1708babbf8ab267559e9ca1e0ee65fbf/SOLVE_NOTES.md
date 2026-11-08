# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private
answers, audit evidence, or prior solution explanations. I used only the visible
examples printed by `blind prepare` and my own matrix calculations.

## Revision 1 — infer a panel-to-panel symmetry and apply it to the payload

The grid has one header row followed by three `n × n` panels separated by two
columns of color 8, where `n = input_height - 1`. The first two panels demonstrate
one of the eight square symmetries. Applying that same symmetry to the third
panel gives the output mask. Its nonzero cells are recolored with the leftmost
nonzero color in the header row; zeros remain zero.

Checks on the demonstrations:

- Example 0: the second panel is an anti-diagonal reflection of the first. The
  same reflection maps the color-7 payload to the displayed color-3 output.
- Example 1: the second panel is a 90-degree counterclockwise rotation of the
  first. The three horizontal color-1 cells become the vertical color-7 output.
- Example 2: the second panel is a top-bottom reflection of the first. The same
  reflection maps the color-3 payload to the displayed color-2 output.

The extra header colors in example 1 show that the output marker is not merely
"the only header color"; across all three examples it is consistently the
leftmost nonzero header cell. I enumerate the eight dihedral transforms, select
the one mapping panel 1 exactly to panel 2, apply it to panel 3, and normalize
all payload foreground cells to the marker color.

Predictions:

- Query 0 demonstrates a top-bottom reflection and should output the vertically
  flipped six-by-six payload in color 6 (the leftmost nonzero header marker).
- Query 1 demonstrates a 90-degree counterclockwise rotation and should output
  the rotated four-by-four payload in color 9.

Remaining uncertainty: a perfectly symmetric demonstration panel could admit
multiple transforms that act differently on the payload. No visible example or
query appears to have that ambiguity, so the implementation uses a deterministic
canonical transform order rather than inventing an unsupported disambiguator.
