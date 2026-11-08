# Post-repair solve notes

This is a human work log from the visible examples in `challenge.json`. I had
already seen the task rule while reviewing the generator, so this is **not** a
blind solve; the finish declaration will record earlier exposure honestly. I did
not consult the generator, Racket source, reference solution, or private labels
while solving this episode.

## Revision 1

Hypothesis from the three visible examples: each nonzero color occurs twice. The
two cells mark opposite corners of that color's axis-aligned bounding box. The
output paints every cell in that inclusive box. This includes horizontal and
vertical degenerate boxes, as shown by color 2 in train 0 and color 5 in train 2.

Probe: implement the hypothesis directly for every color with exactly two
occurrences, preserving grid size and background. The two visible test inputs
then require a 3x3 color-6 rectangle plus a horizontal color-9 line, and a 3x4
color-1 rectangle plus a vertical color-4 line, respectively.
