# Solve work log

## Exposure declaration

I had already inspected this generator and its canonical rule while performing the assigned review, so this is **not a blind solve**. For this solve phase I did not reopen the generator, Racket rule, reference solutions, private labels, or prior solve explanations. I used only `solve/challenge.json`, the visible presentation in `solve/README.md`, and the check command's visible-example feedback.

## Revision 1 — structural frame propagation

### Observations from the visible demonstrations

- Every non-blue object is a hollow monochrome 4×4 frame.
- Blue (`1`) cells form runs on the outer boundary and do not survive in the output.
- A boundary run points inward at a frame whose row span (left/right run) or column span (top/bottom run) overlaps the run.
- The selected frame is copied repeatedly **toward** that boundary in four-cell strides. A final copy may be clipped by the grid edge.
- All original frames remain. With two frame colors, each propagated chain keeps the selected frame's own color.
- Partial blue runs in the examples indicate that overlap, rather than exact equality of spans, selects the frame.

### Implementation

`solution.py` independently detects exact hollow 4×4 frames, finds 4-connected blue boundary components, infers their edge direction, selects the unique frame with positive maximum perpendicular overlap, and draws clipped copies every four cells toward the edge. It starts from a blank canvas, redraws every original frame, and omits the blue markers.

### Alternatives considered

A weaker rule could extend only once, use one global frame color, require a full four-cell marker, or fill a solid corridor. The visible examples reject those: long paths need multiple copies, the multicolor example preserves separate colors, partial markers still act, and repeated hollow boundaries/intersections explain the output exactly.

### Remaining uncertainty

The visible examples appear to identify the rule well, but hidden cases could in principle include malformed/non-unique markers or conflicting differently colored propagated frames. The generated examples look deliberately constrained to avoid those conditions, so the solver raises on ambiguous marker-to-frame matching rather than inventing a tie-break.
