# Solve notes

Earlier exposure: yes. I had already reviewed the task while repairing its generator, so this is intentionally not claimed as blind. During this solve episode I used only the visible examples in `README.md` and did not reopen the Racket rule, generator, reference labels, or earlier solution notes.

## Hypothesis

The nonzero objects have distinct roles:

- the red cells are the source polyomino;
- the blue cell's corner encodes quarter-turns clockwise: top-left 0, top-right 1, bottom-right 2, bottom-left 3;
- the vector from the green cell to the orange cell translates the rotated red shape;
- the output is an otherwise-zero grid with the resulting cells recolored 8.

The examples deliberately reuse a top-right blue control with different green-to-orange vectors, ruling out a fixed displacement for that corner. I implemented the geometric rule directly, using the red bounding-box origin before rotation and normalizing after each quarter-turn.

## Checks considered

- Example 0: top-right means one clockwise turn; green `(8,2)` to orange `(10,5)` gives `(2,3)`, placing the four-cell staircase at the shown cyan coordinates.
- Example 1: the same top-right corner has vector `(-3,-2)`, so displacement is read from the markers rather than memorized by corner.
- Example 2: bottom-left means three clockwise turns and vector `(2,3)`; the output orientation and placement match.
- Examples 3 and 6 exercise bottom-right/bottom-left rotations and noncanonical vectors.

One implementation revision was sufficient because all seven visible examples exercise the proposed rotation/translation decomposition.
