# Solve work log

I had not opened any generator, Racket rule, canonical answer, prior solution, audit record, or repair target before this solve. I used only the visible examples printed by `review.py blind prepare` and the public solve files.

## Revision 1

Hypothesis: one color is used twice: once as an isolated single-cell marker and once as a larger 4-connected object. The output is the tight bounding-box crop of that larger object, preserving its color and using zero for holes/background.

Evidence from all four demonstrations:

- Example 0: color 4 has a singleton at the top and a four-cell object shaped like the 2x3 output.
- Example 1: color 7 has a singleton and the five-cell 3x2 output object.
- Example 2: color 8 has a singleton and the five-cell 3x3 output object.
- Example 3: color 2 has a singleton and the four-cell 3x2 output object.

Other colors can form one or more distractor objects, so total color count alone is insufficient. I implemented per-color 4-connected components, selected a color with both a singleton and a non-singleton component, then cropped its largest non-singleton component. Remaining uncertainty: the visible examples contain a unique marked color; the implementation uses the largest qualifying object if malformed data contains more than one.
