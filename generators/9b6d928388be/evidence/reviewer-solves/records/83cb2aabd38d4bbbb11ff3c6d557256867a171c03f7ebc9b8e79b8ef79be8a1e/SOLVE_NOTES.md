# Solve work log

I had no earlier exposure to this task's rule, generator, private labels, or prior
solutions. I used only the visible grids created by `review.py blind prepare` and
small Python probes over `challenge.json`.

## Revision 1 — size-ranked shapes placed in numbered frames

The inputs contain three loose colored objects, three complete color-5 rectangular
outlines, and singleton markers 1, 2, and 3 immediately above those outlines.
The output erases each loose object and overlays it into the frame bearing its
rank. The ranks are increasing colored-cell count; the first training pair has a
tie at eight cells, resolved by top-to-bottom/left-to-right reading order. The
object's bounding box is centered in the frame, with odd slack biased upward and
left. Zero cells inside the object's bounding box are transparent, so the frame
remains visible through holes.

I wrote a component-based prototype and replayed all three visible training pairs.
It identified the frame bounds, marker-to-frame pairing, object counts, and exact
placement; all three reconstructed outputs matched cell-for-cell. The submitted
solver uses the same logic without consulting any hidden answer or reference.

Remaining uncertainty: the visible set does not establish behavior for malformed
inputs, missing markers, disconnected objects, or ties beyond reading order. The
implementation handles the demonstrated three-object contract and leaves unmatched
markers unchanged rather than guessing.
