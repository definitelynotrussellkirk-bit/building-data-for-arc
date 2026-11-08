# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, canonical rule, notes, audit records, or any earlier solution. I used only the visible challenge printed by `review.py blind prepare` and the generated solve files.

## Revision 1 — frame inheritance

**Hypothesis.** Each large, single-color hollow rectangle is a container. Every non-background cell strictly inside a container is recolored to the container border's color. When containers are nested, the outermost container wins. Unframed objects remain unchanged.

**Evidence from the visible examples.** In example 0, the orange block inside the blue frame becomes blue, while the nested azure frame and green block both become the enclosing maroon color. The isolated red cells and yellow cell remain unchanged. Examples 1 and 2 repeat the same behavior with different frame sizes, colors, nesting depth, and unrelated outside objects.

**Implementation.** Find four-connected monochrome components that are exactly the perimeter of an axis-aligned bounding rectangle with a nonempty interior. Recolor non-background cells inside each rectangle. Process smaller rectangles first and larger rectangles last so an enclosing frame overrides an inner one.

**Alternatives considered.** Recoloring each nonzero component to the color of the largest object would incorrectly change isolated distractors. Recoloring only the immediate contents of each frame would leave inner-frame colors in nested examples. Treating every rectangular block as a frame is harmless for height/width below three but unsafe for larger filled blocks, so the detector requires an exact hollow perimeter.

**Remaining uncertainty.** The visible examples all use background color 0 and fully closed one-cell frames. The implementation infers the most frequent color as background and requires exact four-connected rectangular perimeters. Query correctness remains hidden.
