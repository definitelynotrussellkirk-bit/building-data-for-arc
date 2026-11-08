# Post-repair visible-example solve notes

This is a human-readable work log, not a hidden model trace. I had earlier rule
exposure while reviewing this assigned generator, so the final declaration must
be `earlier-exposure yes`. During this solve phase I did not reopen the Racket
rule, generator source, reference solutions, or private labels.

## Hypothesis from the displayed examples

Each nonzero color forms one rectangular frame. Exactly one frame has extra
same-colored cells in its interior. Its outer dimensions define the selected
frame class and its interior cells define a relative pattern. The output:

1. keeps the patterned frame and all empty frames with the same dimensions;
2. copies the relative interior pattern into each kept frame using that frame's
   own color; and
3. clears every differently sized frame to background 0.

Evidence: in train 0, the patterned color-2 frame is 6x7; colors 9, 8, and 1
share that size and receive the color-2 pattern, while differently sized colors
5 and 7 disappear. The other two examples show the same size-selection and
recoloring rule with different template sizes and distractor positions.

## Implementation

Parse each color's bounding box, take interior same-color cells as the pattern,
identify the unique nonempty template, create an all-zero output, and redraw
only frames with the template's exact outer shape plus the translated pattern.
