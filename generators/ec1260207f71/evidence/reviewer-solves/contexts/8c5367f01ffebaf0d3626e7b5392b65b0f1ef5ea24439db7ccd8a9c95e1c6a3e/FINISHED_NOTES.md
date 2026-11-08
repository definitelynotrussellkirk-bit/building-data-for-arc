# Solve work log

Earlier exposure: none. I did not inspect any generator, rule, solution, task notes, or private labels before this solve.

## Hypothesis 1

Each input has two equal-height vertical red bars on opposite sides. Azure points occur only in the row band of one bar. For every azure point, the output (a) paints azure between that bar and the point, recolors the point green, and (b) activates the same relative row of the opposite bar by painting from that bar to the far edge. Blank relative rows remain blank.

Evidence from all three visible pairs:
- Pair 1 activates relative rows 2, 3, 4, and 6 on both six-cell bars.
- Pair 2 activates relative rows 2, 3, and 5 on both five-cell bars.
- Pair 3 activates relative rows 2, 4, and 5 on both five-cell bars.
- On the marker-bearing side, only the segment between red bar and azure endpoint is filled and the endpoint changes 8 -> 4.
- On the opposite side, the entire inward span is filled with 8.

Implementation detects the two vertical red components, selects the one whose row band contains inward azure markers, maps rows by offset from each bar's top, and applies the two fills. Remaining uncertainty is limited to malformed inputs (unequal bar heights, no markers, or more than two bars); the solver leaves those unchanged rather than guessing.
