# Solve notes

## Prior exposure

This is not a blind solve. Before `prepare`, I reviewed and repaired the assigned generator and saw the task's rule sources. From `prepare` onward I kept generator, Racket, references, and private labels closed and used only `solve/challenge.json`.

## Visible-example inference

All outputs are blank same-size grids except for color 6. Color-2 cells on the top edge behave like downward emitters; color-1 cells on the left edge behave like rightward emitters. With no color-5 cells in the third training example, every top-emitter column crosses every left-emitter row and all eight crossings become 6.

Color 5 blocks propagation. In training example 1, the blocker at row 3 / emitter column 2 removes the lower crossings in that column, and the blocker immediately right of the row-5 emitter prevents that horizontal ray from reaching either column. In training example 2, the blocker in column 8 removes its lower crossings and the blocker on row 7 stops that row before column 3. These observations support directional ray stopping rather than merely deleting crossings that themselves contain a 5.

## Selected algorithm

1. Collect every top-edge column containing 2.
2. Cast a vertical ray downward from each, stopping before the first 5.
3. Collect every left-edge row containing 1.
4. Cast a horizontal ray rightward from each, stopping before the first 5.
5. Return a zero grid with 6 at the intersection of the two reached-cell sets.

The implementation preserves the input and supports arbitrary rectangular dimensions.
