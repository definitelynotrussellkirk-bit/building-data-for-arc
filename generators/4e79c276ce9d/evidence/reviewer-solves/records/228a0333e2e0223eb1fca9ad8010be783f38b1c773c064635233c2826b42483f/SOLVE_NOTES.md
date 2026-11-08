# Blind solve notes

## Evidence boundary

I read only the public WORK/solve-blind/README.md and challenge.json. I have not read a Racket rule, generator source, reference solution, canonical data, private labels, previous solution notes, or other task files. The initial public-read command found README.md but challenge.json was not ready; after the parent reported successful preparation, I read the two public files. That initial missing-file read was not a solver attempt.

## First hypothesis

Ignore color 0 as background. Partition each other color into components connected through shared horizontal or vertical edges. Select the component with the fewest occupied cells. Return its tight bounding box, preserving the component color and placing zeros at unoccupied positions inside the box.

The visible evidence is:

- Demonstration 0 has components of sizes 4 (color 3), 3 (color 5), 2 (color 7), and 5 (color 8). Its output is the size-2 color-7 component.
- Demonstration 1 has components of sizes 6 (color 8), 7 (the upper-left color-9 piece), 5 (the lower-right color-9 piece), and 8 (color 2). Its output is the size-5 color-9 piece, cropped to 2 rows by 4 columns.
- Demonstration 2 has components of sizes 7 (the upper color-9 piece), 8 (color 7), 6 (color 2), and 5 (the lower color-9 piece). Its output is the size-5 color-9 piece, cropped to 4 rows by 2 columns.

The color-9 pieces touch diagonally in demonstrations 1 and 2. Therefore diagonal contact must not join components under this hypothesis. Counting whole colors would also fail: color 9 has 12 cells in both examples, but the outputs contain only 5. Components of different colors may touch through an edge, as in demonstration 0, so connectivity must require a matching color.

The observations do not establish behavior for equal smallest sizes, inputs without objects, or nonzero backgrounds. The implementation uses the first component encountered in row-major order for ties, rejects an empty-object input, and treats zero as background. None of these unresolved cases occurs in the visible inputs.

## Predicted masked queries

Applying the same rule to query 0 predicts [[8, 8]]. Query 1 predicts [[3, 3, 3, 3], [3, 0, 0, 0]]. These are predictions based on the visible inputs, not observations of private expected answers.

## Real attempt log

Attempt 1: implement the smallest monochromatic edge-connected component rule. The first official check will test this implementation because it directly explains all three examples and distinguishes the diagonal-touching pieces. No solver attempt has been discarded or fabricated.
