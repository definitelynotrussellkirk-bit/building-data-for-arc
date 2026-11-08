# Solve work log

## Prior exposure

Before this visible-only solve I had already reviewed the assigned generator and canonical rule as required by the repair task. I therefore have earlier rule exposure and will record `--earlier-exposure yes`. During this solve I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations; I used only `solve/challenge.json` and the visible pairs above.

## Revision 1 — parity-conditioned frame centers

Visible observations:

- Every colored object is a one-cell-thick hollow rectangular frame.
- A 3×3 frame gains its color in the middle cell.
- Other odd-by-odd examples (3×5, 5×3, 5×5) likewise gain exactly the bbox-center cell.
- Frames with either even height or even width are unchanged: visible examples include 3×4, 4×3, and 3×4 frames.
- Existing frame pixels and all background outside the selected center remain unchanged.

Hypothesis: find each nonzero same-color 4-connected component, verify that it equals the perimeter of its bounding box, and paint the unique center only when both bbox dimensions are odd. This distinguishes the intended rule from the tempting shortcut “mark every frame at a rounded/floor center.”

Implementation notes: the solver copies the input, detects exact frame perimeters rather than assuming every component is a frame, and uses integer midpoint coordinates only after the odd/odd test. I expect test query 1 to leave the 7×4 color-9 frame unchanged and mark the 7×5 color-5 frame; query 2 should mark the 3×3 color-4 and 5×3 color-2 frames while leaving the 5×6 color-1 frame unchanged.

Remaining uncertainty: none on the visible examples; private-query correctness is intentionally unavailable.
