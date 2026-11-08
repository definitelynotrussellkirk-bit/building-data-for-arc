# Visible-only solve log

Earlier exposure: yes. I repaired this generator before this solve, so this is an exposed post-repair solve. During this solve I did not reopen the generator, Racket rule, reference answers, or earlier solution explanations; I used only the displayed examples.

## Hypothesis

The three color-9 rectangular components are gallery frames. A colored dot centered immediately above each frame is its key. The nonzero cells inside the frame form a colored shape, cropped to its bounding box.

The last two rows are an ordered program: each occupied column contains a gallery key on the penultimate row and a transform code on the final row. From the demonstrations:

- code 5 leaves the cropped shape unchanged;
- code 6 rotates it 90 degrees clockwise;
- code 7 mirrors it left-to-right.

Transform the requested shapes in program order, top-align them, and concatenate them horizontally with one zero column between adjacent shapes. The output height is the maximum transformed-shape height; its width is the sum of transformed widths plus the separators.

## Checks against the demonstrations

Example 1 disambiguates all three operations: the key-2 shape under code 6 becomes its clockwise rotation; the key-4 shape under code 5 is unchanged; and the repeated key-2 shape under code 7 is horizontally mirrored. Examples 0 and 2 confirm repeated keys and variable cropped widths.
