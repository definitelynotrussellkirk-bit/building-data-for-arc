# Solve work log

## Access declaration
No earlier rule exposure and no reference consultation. Read only the prepared challenge.json, README.md, summary.json, solution.py, and SOLVE_NOTES.md. The permitted summary includes generation provenance metadata; no generator, Racket rule, canonical data, private labels, task notes, audit evidence, or prior solution explanation was opened.

## Revision 1
Hypothesis: each color (3 and 8) supplies two equal-height vertical bars. Preserve the bars, then extend both ends upward and downward in outward staircases. A horizontal move of one column occurs after every segment whose height equals that color's original bar height. The left branch moves left and the right branch moves right. Clip at grid edges. Intersections between colors become 6.

Visible probes: inspected all three input/output pairs, with shapes 22 rows x 18 columns, 23 rows x 17 columns, and 24 rows x 19 columns. Their bar heights differ, including a one-row cyan seed. Examples 1 and 2 show color 6 exactly where the two extended colors coincide. This rules out always using unit-height steps, extending downward only, and giving either color priority at intersections. No candidate was executed before revision 1.

Implementation: derive each color's seed row interval and left/right columns; for every output row compute ceiling(distance from seed interval / seed height), then paint both outward branches. Compose layers with color 6 at overlaps.

Validation command: official blind check with intent solve. Result to be recorded after execution. Remaining uncertainty: only visible examples can be verified; the two query labels remain masked.
