# Solve work log

## Exposure declaration

Before this visible-only episode I had already inspected and repaired the assigned generator and its canonical authority, so this is **not blind**. During the episode itself I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solutions, or private query labels.

## Visible-example inference

All six examples have two isolated nonzero cells at `(0, 0)` and `(0, 1)`, a blank separator, and one later nonzero object. The output is the tight crop of that later object, with every occupied cell recolored to the second control value. The first control value selects a geometric operation.

Comparing the cropped binary object to each output gives the complete table:

- code 1: identity (example 0);
- code 2: left/right reflection (example 1);
- code 3: up/down reflection (example 2);
- code 4: 90° clockwise rotation (example 3);
- code 5: 180° rotation (example 4);
- code 6: 90° counterclockwise rotation (example 5).

I implemented a shape-safe crop over nonzero cells below row 0, converted it to a binary mask, applied the indicated transform, and recolored occupied cells with `grid[0][1]`. This also predicts query 0 by identity and query 1 by left/right reflection. No alternative visible rule remained after the six examples because each code is represented exactly once.
