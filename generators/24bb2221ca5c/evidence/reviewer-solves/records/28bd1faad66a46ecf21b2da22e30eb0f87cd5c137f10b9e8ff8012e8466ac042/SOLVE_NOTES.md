# Solve work log

This is a human-authored work log. I had **earlier exposure** to the task rule and to the preceding round's generator work, so this is not evidence of an unprimed solve. After the new `prepare` step I consulted only `solve/challenge.json`, my own Python program, and visible checker feedback; I did not consult the generator, Racket authority, reference solutions, private labels, or the earlier solution.

## Revision 1

### Visible evidence

- Training example 0 has two closed monochrome frames. Every zero inside each frame becomes the frame color.
- Training example 1 contrasts a closed color-3 frame, which fills, with a color-4 frame that has a wall gap, whose zero interior remains unchanged. This rules out filling every component bounding box.
- Training example 2 uses two disconnected objects of the same color. The first is a one-chamber frame. The second contains a divider and therefore multiple enclosed zero regions, plus a protruding cell. All enclosed regions fill, but zeros exposed by the protrusion remain zero. This rules out treating all cells of one color as a single bounding-box object and rules out filling only one hole per component.

### Hypothesis

For each monochrome 4-connected nonzero component independently, inspect its bounding box. Flood-fill bbox-local zero cells reachable from the bounding-box edge. Recolor every remaining zero region with that component's color. Preserve existing nonzero cells and exterior-connected zeros.

### Implementation

`solution.py` extracts same-color 4-connected components, performs an edge flood-fill over zero cells inside each component bounding box, and fills the complement. It processes disconnected same-color components separately and fills all enclosed regions, not merely the largest or first.

### Local visible probe

I ran the program on all three visible training inputs from `challenge.json` and compared its outputs exactly with the visible outputs before invoking the official check. All three matched. The masked test outputs remain unknown.

### Alternatives rejected

- Fill each nonzero bounding box: contradicted by the gapped color-4 object.
- Fill only rectangular frames: contradicted by the spurred/divided object.
- Merge disconnected cells by color: contradicted by the two separate color-1 objects.
- Fill one enclosed region per object: contradicted by the divided object.
