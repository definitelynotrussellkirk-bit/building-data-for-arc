# Solve work log

## Exposure statement

Before this blind solve I read only the packet-level instructions and the visible
challenge produced by `python3 review.py blind prepare`. I did not open any
Racket rule, generator implementation, reference solution, private query label,
notes, or audit evidence for this task or for the later repair target.

## Revision 1 — centered recolored template

**Hypothesis.** Color 2 is a small template. Every other non-background color
forms a hollow rectangular frame. Remove the red template, copy its exact binary
shape into the interior of every frame, center it using the upper/left choice
when a one-cell tie exists, and recolor the copy to the frame color.

**Evidence from the visible examples.**

- Example 0 has a 3×3 red L. It fills the 3×3 interior of the small frame and is
  centered unchanged inside the 5×5 interior of the large frame.
- Example 1 has a 2×3 zig-zag. The same orientation appears in both frames,
  centered in their differently shaped interiors.
- Example 2 has a mirrored 3×3 L. Its orientation is again preserved, ruling out
  a fixed hard-coded glyph or a rotation toward the frame.
- A frame can touch/overwrite one boundary cell of another frame. Per-color
  bounding boxes still recover both frame extents in the visible examples.

**Implementation.** Find the red bounding-box mask, erase its original cells,
find each other color's bounding box, and stamp the mask at the centered offset
inside that box. The implementation deliberately uses the original grid for
object detection so one stamped copy cannot affect later frame detection.

**Remaining uncertainty.** The visible examples support one red component and
one frame per non-red color. The solution assumes those conditions and skips a
frame if its interior cannot contain the template.
