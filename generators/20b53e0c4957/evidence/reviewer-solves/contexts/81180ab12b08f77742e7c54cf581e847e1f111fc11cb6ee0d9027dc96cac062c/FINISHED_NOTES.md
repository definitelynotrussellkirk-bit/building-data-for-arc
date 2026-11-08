# Solve work log

Earlier exposure: **yes**. Before this visible-only episode I had repaired and tested the assigned generator and therefore already knew the intended rule family. During this solve I consulted only the prepared visible challenge/README and my own code; I did not consult the Racket authority, generator source, reference solutions, private labels, or prior solve notes.

## Revision 1

Hypothesis from the visible examples:

- Two full-height color-5 columns divide the input into equal panels A, B, and C.
- A and B share coordinates and color. Cells present in A but absent from B encode a cutout mask.
- The mask is expressed relative to A's occupied bounding-box origin, not as raw panel coordinates.
- Translate those offsets to C's occupied bounding-box origin and erase those cells from a copy of C. Preserve C's pre-existing holes and all background outside C.

Why bbox-relative rather than copying/recoloring B: train examples 0 and 2 translate the C object relative to A/B, and C has an independent hole that the output preserves. The direct B-copy alternatives therefore disagree with the shown outputs.

Implementation: locate the two divider columns, split panels, compute occupied sets and A/C bbox origins, form `A - B`, translate each removed coordinate from A's origin to C's origin, and zero it in C.

Remaining uncertainty: none for the visible domain; malformed inputs deliberately raise a clear error rather than silently guessing a different panel layout.
