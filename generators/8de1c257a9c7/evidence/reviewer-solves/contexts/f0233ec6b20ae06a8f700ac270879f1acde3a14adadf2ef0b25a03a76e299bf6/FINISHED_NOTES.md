# Post-repair visible-only solve notes

## Exposure declaration

I had already inspected this task's generator while performing the assigned review, so this is an exposed post-repair solve rather than a blind solve. During this solve phase I used only the public examples in `solve/README.md`; I did not reopen or consult the Racket rule, generator source, private labels, reference solutions, or prior solve explanations.

## Observations

- Every input has one green cell (3), a connected cyan shape (8) around it, and one or more red cells (2).
- The output clears the source drawing and all markers.
- Relative to each red cell, the output reproduces every cyan offset measured from the green cell.
- Train example 0 makes this especially direct: the ten-cell cyan shape around the green is copied to both red markers, giving twenty cyan cells.
- Train example 2 has four red markers and a four-cell cross template. Overlap reduces the union to twelve output cells, so copies combine by set union rather than XOR or overwrite with another color.
- Train examples 1 and 3 use asymmetric templates. Their outputs preserve the template orientation, rejecting rotation or horizontal mirroring.

## Implemented hypothesis

1. Locate the unique green anchor.
2. Record all cyan coordinates as offsets from that anchor.
3. Create an all-zero output with the same dimensions.
4. For each red marker, place color 8 at every translated offset that remains in bounds.

The implementation validates rectangularity and the unique-green assumption, while retaining an in-bounds guard for robustness.
