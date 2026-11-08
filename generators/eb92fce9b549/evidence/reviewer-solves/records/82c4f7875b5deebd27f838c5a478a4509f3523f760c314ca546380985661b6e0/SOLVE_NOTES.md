# Solve work log

I had not opened this task's generator, Racket rule, private labels, prior solve
notes, or the assigned repair target before solving. I used only the prepared
visible examples.

## Revision 1

The nonzero cells split into four-connected objects. The two small-grid examples
repeat the same three shapes under different positions/orientations: a five-cell
L becomes color 2, a filled 2x3 rectangle becomes color 3, and a four-cell line
becomes color 4. The large example contains separate concentric square frames
with side lengths 13, 9, and 5 plus a center singleton; these become colors 2,
3, 4, and 5 from outside inward. This suggests that geometry encodes the output
color while the original foreground color is irrelevant.

I implemented four-connected component extraction plus explicit recognizers for
those visible glyph families. For square frames, the observed side lengths obey
`side = 1 + 4 * (5 - output_color)`. Query 0 repeats the exact nested geometry in
a different source color. Query 1 contains a filled 2x3 rectangle and a rotated
five-cell L, so the same recognizers apply.

Remaining uncertainty: the demonstrations do not show every possible geometric
encoding or scale. The implementation deliberately preserves any unrecognized
component rather than inventing a broader rule.
