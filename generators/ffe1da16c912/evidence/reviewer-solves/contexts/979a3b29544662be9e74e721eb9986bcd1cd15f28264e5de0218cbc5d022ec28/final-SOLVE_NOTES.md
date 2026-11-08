# Fresh solve notes

## Constraint acknowledgement

During this solve phase I inspected only `solve/challenge.json` plus the solution and notes I authored. I did not reopen the generator, Racket rule, canonical ledger, reference outputs, private labels, or earlier written explanations. I had seen the task rule before this phase while doing the assigned generator review, so this is not a blind solve and will be marked `earlier-exposure=yes`.

## Hypothesis 1: four panels, with the fourth selecting a prototype family

Every input is three rows by fifteen columns, with solid color-5 columns separating four 3x3 panels. The first three panels each contain one monochrome shape. The fourth contains another monochrome shape in the color used by the output.

Probe: compare occupied-cell counts and normalized supports in each visible training pair. In each case, the fourth panel has the same occupied-cell count as one of the first three, and its support is a rotation or reflection of exactly one prototype. The output uses that prototype's displayed orientation, tightly cropped, but recolored with the fourth panel's color.

## Alternatives checked

- **Copy the fourth panel directly:** ruled out because training outputs restore the matched prototype's original displayed orientation rather than preserving the query orientation.
- **Choose only by occupied-cell count:** ruled out because multiple prototypes can have equal area; shape equivalence under rotations/reflections is needed.
- **Keep the prototype's color:** ruled out because every visible output uses the query panel's color.
- **Output an index or full 3x3 panel:** ruled out because outputs are tight bounding boxes of the selected prototype support.

## Implementation

Split the input into four 3x3 panels. Normalize supports to their tight bounding boxes. Enumerate the eight square-grid rotations/reflections of each prototype and select the first family matching the query support. Paint the selected prototype support in its displayed orientation using the query color, on a tight zero background.
