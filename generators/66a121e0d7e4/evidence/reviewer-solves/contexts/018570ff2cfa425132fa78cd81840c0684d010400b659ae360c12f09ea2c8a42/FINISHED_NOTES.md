# Visible-only solve notes

I had earlier rule exposure from repairing this same generator, so this is not a blind inference record. I did not consult the generator, Racket rule, private labels, or earlier reference solution after the solve episode was prepared.

The visible examples independently support the following reading:

- The upper-left value is a command in 1..4.
- Color 8 in the left header selects payload rows; color 8 in the top header selects payload columns.
- Read the exact row/column intersections in their original order.
- Command 1 leaves that matrix unchanged; 2 rotates it clockwise; 3 rotates it 180 degrees; 4 rotates it counter-clockwise.

Shape checks make the rotations unambiguous: example 1 extracts a 2x4 matrix and outputs 4x2 under command 2, while example 3 extracts 3x4 and outputs 4x3 under command 4. I implemented the rule generically with no fixed selector count.
