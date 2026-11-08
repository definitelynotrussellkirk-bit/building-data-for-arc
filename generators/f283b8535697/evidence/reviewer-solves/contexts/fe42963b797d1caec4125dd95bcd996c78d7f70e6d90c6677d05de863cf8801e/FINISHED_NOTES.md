# Solve work log

Earlier exposure: none. I did not open this task's generator, rule, notes,
solutions, audit records, or the assigned repair generator before solving.

## Revision 1

The inputs are 24x24 patterns with a filled 5x5 rectangle of color 1, while
the outputs are 5x5 and contain no 1s. The surrounding pattern is symmetric
across the horizontal midline (top/bottom reflection). I tested the hypothesis
that the output is the content hidden by the 1-rectangle, recovered from the
vertically mirrored location.

For the first training pair, the mask occupies rows 19..23 and columns 10..14.
Reflecting those rows through the 24-row grid gives rows 4..0 at the same
columns; these five rows exactly equal the shown output. The second mask at
rows 3..7 similarly maps to rows 20..16 and reproduces its output. The third
pair agrees as well.

The implementation locates the full rectangle of 1s, validates that it is
solid, and returns values from row `height - 1 - r` at the same columns. I
considered left/right reflection and 180-degree rotation, but the first pair's
non-symmetric local details distinguish them; top/bottom reflection is the
operation matching all visible examples.

Remaining uncertainty: the hidden test masks might touch the horizontal axis,
but the supplied examples and tests place each mask wholly on one side, so its
mirror is visible.
