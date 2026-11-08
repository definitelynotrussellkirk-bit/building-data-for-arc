# Post-repair visible-example solve notes

## Revision 1

The visible examples suggest that color 8 is a passive separator or wall. I treat each 4-connected component of zeros independently. For each zero component, I inspect its cardinally adjacent cells, discard 0 and 8, and collect the remaining distinct colors.

- If there is exactly one distinct adjacent color, fill the entire zero component with that color.
- If there are no adjacent colors or two or more distinct adjacent colors, leave it unchanged.
- The number of adjacent cells does not matter: train example 1 has two color-9 seed cells around one chamber and a color-4 frame around another, while both regions fill. Its mixed color-2/color-3 chamber stays zero. The edge-connected color-1 region fills, so enclosure is not required.

The implementation uses a breadth-first search over each zero component and applies this rule without changing nonzero cells or dimensions.
