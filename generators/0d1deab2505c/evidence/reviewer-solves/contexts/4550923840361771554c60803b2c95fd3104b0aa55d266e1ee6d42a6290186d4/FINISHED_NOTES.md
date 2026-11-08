# Post-repair visible-only solve: 0d1deab2505c

Assignment: review-44f307c1cb52a1c8.
Generator hash supplied for provenance: 24b57d0c9c06922e455ca7e97cef32a520e835c3a1cba6d036c20e809122764d.

## Exposure and scope

This is the official post-repair solve, not a blind episode. Earlier exposure is YES at session level because the parent conducted generator repair before this step. This solver phase itself read only solve/README.md and solve/challenge.json and the prepare command's visible-example output. No generator, Racket rule, canonical data, private output, reference implementation, prior task solution explanation, or evidence probe was consulted during this phase. Reference consulted during solve: NO.

## Observations from the three visible demonstrations

Color 8 is the background. Each distinct figure has a color-4 center with a differently colored orthogonal neighbor on each side, followed by a color-1 straight stem on one side. Some stems end in a diagonal pair of 1s; some end without that pair. The five-cell colored cross is a useful local anchor. Eight-neighbor connectivity keeps diagonal terminal cells with their figure.

- Example 0: the cross center moves from (2,2) to (1,2), placing its upper tip at the top boundary. The downward stem translates upward by one without changing its arrangement. The cross swaps its top/bottom colors and its left/right colors.
- Example 1: rightward stems send their crosses to column 1; the leftward stem sends its cross to column 19 in a width-21 grid. Stem lengths and terminal pairs are preserved. All three crosses make the same two opposite-color swaps.
- Example 2: downward stems send crosses to row 1. The upward-stem figure moves from center (6,1) to (12,1), placing its lower tip at row 13 in the height-14 grid. Again only the colored cross rotates; stem orientation stays fixed.
- Visible query 0 has one upward-stem figure. Query 1 has four separated upward-stem figures, including both straight and forked terminals. Their output labels are unavailable.

## First hypothesis and implementation

For each eight-connected non-background figure, identify its color-4 center and the cardinal direction of the blue stem by the cell two steps from that center. Translate the whole figure in the opposite direction until the cross tip reaches the corresponding grid boundary. Rotate just the five-cell cross by 180 degrees around its translated center. Preserve the stem as translated.

The implementation reconstructs a grid of the original dimensions. It treats color 0 as a real foreground color whenever present. It rejects ambiguous centers, ambiguous stems, out-of-grid transforms, and output overlaps rather than silently dropping cells. Such rejection cases are not established behavior by these demonstrations; every visible figure has exactly one center and one stem.

This is the first genuine solver revision. I will use the official local Python visible-only check to test the complete three-example rule. No alternate failure, private success, or hidden-target result has been invented.
