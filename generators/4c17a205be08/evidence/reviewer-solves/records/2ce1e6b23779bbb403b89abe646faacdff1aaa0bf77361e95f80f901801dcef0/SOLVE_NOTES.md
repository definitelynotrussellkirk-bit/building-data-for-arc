# Solve work log

## Exposure declaration

I had already inspected this task's generator and Racket-facing verification before this fresh solve. I therefore have **earlier rule exposure** and will declare it at finish. After `prepare`, I consulted only `solve/challenge.json`, wrote this Python implementation from the public grids, and used only visible-example feedback from `solve_episode.py check`. I did not consult the generator, Racket rule, prior solve files, reference solutions, or private query labels during this episode.

## Revision 1 hypothesis

Every public input has three five-column panels separated by two full-height columns of color 9. In each panel, surrounding zero rows and columns are padding, so I crop to the nonzero bounding box.

Across the five demonstrations, the first cropped panel is mapped to the second by one member of a six-operation family: identity, clockwise rotation, 180-degree rotation, counter-clockwise rotation, left-right reflection, or up-down reflection. The public output is the same operation applied to the cropped third panel.

Implementation plan:

1. Detect the two full-height color-9 separator columns and split the input into three panels.
2. Crop each panel to its nonzero bounding rectangle.
3. Evaluate the six candidate transforms in a fixed order and select the one whose transformed first crop exactly equals the second crop.
4. Apply that transform to the third crop and return it.

The examples appear deliberately asymmetric, so I expect a unique exact match. I will stop after one revision if it passes all five visible demonstrations; masked query correctness remains unknown by policy.
