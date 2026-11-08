# Solve work log

## Exposure declaration before solving

I had not opened task `b7c3b8bc9805`'s generator, canonical rule, notes,
solutions, labels, or audit records. I used only `solve-blind/challenge.json` and
my own local test script. I had seen only the packet-wide workflow documentation.

## Revision 1 — diagonal block checker inside the gray frame

**Observed transformation.** Every input contains one hollow gray (`5`)
rectangle and two isolated non-gray colors. The output preserves the frame and
both marker pixels. Only the frame interior changes. Its rows and columns are
split into upper/lower and left/right halves, with the extra row or column (for
odd interior sizes) assigned to the upper or left half. One color fills the
upper-left and lower-right blocks; the other fills upper-right and lower-left.

**Ordering hypothesis.** Sort the two marker pixels in row-major order. When the
gray frame width is even, the first marker color is used on the main block
diagonal. When the frame width is odd, the second marker color is used there.
This fits all four visible examples and predicts the two queries consistently:
the 6-wide query starts with color `1`, while the 5-wide query starts with color
`7`.

**Probes.** I wrote `test_visible_examples.py` before implementing the solver.
The initial run failed at the template's `NotImplementedError`, confirming the
test exercised the missing behavior. I then implemented frame detection,
row-major marker ordering, width-parity color selection, and the four-block fill.

**Alternatives considered.** I first considered selecting the leading color from
marker distance, quadrant, or angle relative to the frame. Those rules were
inconsistent across the four demonstrations, especially the below-left example.
The frame-width-parity/row-major rule is the simplest invariant that explains all
four color orderings. Remaining uncertainty is whether the intended authority
uses an equivalent construction rather than explicitly testing width parity.
