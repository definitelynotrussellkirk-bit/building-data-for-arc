# Solve work log

## Exposure statement

Before this solve I had opened only the packet-level instructions. I had not opened
this task's generator, canonical rule, reference solution, private labels, audit
records, or earlier solution explanations.

## Revision 1 — complete vertical reflection inside each frame

**Visible pattern.** Every object is a rectangular border of color 1 containing
some color-4 cells. The output preserves the border and the original 4s. It adds
color 7 exactly at missing counterparts obtained by reflecting the 4s across the
horizontal midline of that rectangle (top and bottom exchange). A counterpart
already occupied by color 4 is left unchanged.

This accounts for all visible cases, including the even-height interiors in train
3 and the three independent frames in train 2. Horizontal reflection is ruled out
by train 1, where marks on the bottom interior row are copied to the top interior
row without changing columns.

**Implementation.** Find 4-connected components of color 1, use each component's
bounding box as its frame, collect interior color-4 cells from the original input,
and color each blank reflected location 7. Reading sources from the unmodified
input avoids newly added 7s influencing later work.

**Remaining uncertainty.** The visible examples use disjoint complete rectangular
frames. The implementation follows that demonstrated domain and does not attempt
to repair malformed or touching frames.
