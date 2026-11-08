# Visible-only solve notes

## Exposure disclosure

I had encountered this task family before this post-repair episode. During this
solve I did not reopen the generator, Racket authority, canonical task, prior
solution, private labels, or any earlier explanation; I used only
`solve/challenge.json`. The episode is therefore marked `earlier-exposure=yes`
and `reference-consulted=no` rather than presented as a genuinely blind solve.

## Hypothesis 0

Each input has one gray (`3`) object and one hollow rectangle in another color.
Take the gray object's tight bounding-box mask, rotate that mask 90 degrees
clockwise, erase the source object, and stamp the rotated object beginning one
row and one column inside the rectangle's top-left corner.

The first two training pairs distinguish an authoritative stamp from a
"preserve the frame" rule: the rotated gray object reaches the rectangle's
right edge and replaces those border cells. The third pair confirms the same
clockwise rotation and top-left anchor when the object fits without touching a
border. All three visible pairs match without revising the hypothesis.

## Test predictions

- Test 1 uses the same five-cell mask as training examples 1 and 3. Its
  clockwise image is `111 / 011`, placed at the top-left interior of the green
  frame; the original gray cells disappear.
- Test 2 rotates `010 / 111 / 001` to `010 / 011 / 110`, places it at the
  top-left interior of the purple frame, and overwrites two cells of the
  frame's bottom border.
