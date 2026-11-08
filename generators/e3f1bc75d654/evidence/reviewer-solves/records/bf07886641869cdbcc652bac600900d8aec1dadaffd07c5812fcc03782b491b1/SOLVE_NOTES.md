# Solve work log

## Prior exposure

I had not opened task `e3f1bc75d654`'s generator, Racket rule, private labels,
reference solutions, audit evidence, or earlier solution notes. I used only the
visible examples prepared in this solve directory.

## Revision 1 — patterned rectangle as a template

Across all three demonstrations, the input contains several monochrome rectangular
frames. Exactly one frame also contains a non-empty interior pattern. In the output:

- that patterned frame remains;
- every hollow frame with the same height and width receives the same binary pattern,
  recolored with its own frame color; and
- frames of other dimensions disappear.

For example, train 0 has a patterned 5x8 color-4 rectangle. The color-6 and color-8
5x8 frames receive its pattern, while differently sized colors 7, 1, and 5 are erased.
The same size-matching behavior holds in trains 1 and 2.

Implementation plan: detect same-color connected components, keep components whose
bounding-box border is a complete rectangle, identify the unique framed object with
colored interior cells, then stamp its boolean mask into every framed object of the
same dimensions. I initialize the output to background so distractors are removed.
The frame component supplies the bounding box, while the mask is read from the whole
box so even a disconnected interior pixel of the source color would be retained.

Before implementation I added a visible-only unit test over all three public train
pairs and confirmed it failed on the template `NotImplementedError`. Remaining
uncertainty is limited to unseen cases that violate the demonstrated contract, such
as multiple patterned templates; the code chooses the one with the most interior
cells defensively.
