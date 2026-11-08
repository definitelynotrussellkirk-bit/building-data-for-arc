# Final-source visible-only solve

This is a reviewer-authored work log, not a captured token-level conversation.
I have earlier exposure from repairing this task. During this fresh episode I
kept the generator, Racket source, reference solutions, private query labels,
and prior solution explanations closed. The previous episode remains under
checks/prior-solve because its generator bytes differ.

## Observation and hypothesis

Example 0: Input: 5 rows × 14 columns. Output: 4 rows × 4 columns.
The two left panels are identical. The output keeps the rightmost panel's
occupied cells and replaces its foreground with the header's first color, 3.

Example 1: Input: 7 rows × 20 columns. Output: 6 rows × 6 columns.
The left and middle panels are completely occupied, so binary silhouettes
cannot distinguish their relation. The three color-2 cells on A's upper right
edge become three cells on B's upper left edge under a quarter turn counter-
clockwise. Applying that turn to the rightmost panel matches the visible
output. Its foreground is 3: the first nonzero header value in [3,5,7,1,6].
The last, smallest, largest, and median header values all disagree with 3.

Example 2: Input: 5 rows × 14 columns. Output: 4 rows × 4 columns.
A half turn maps the exact colored left panel to the middle panel and also
maps the rightmost foreground to the output positions. The color marker is
at the far right of the header, so reading only column zero would fail.

These observations support a common procedure: split the body at full color-8
columns, infer a square symmetry from exact A-to-B colors, apply it to C, and
paint all nonzero output cells with the first nonzero header color.

## Implementation and checks

The native Python solver enumerates rotations of the original and reflected
panel. It accepts a result only when all matching transformations agree on one
output. It neither imports task code nor reads any data file at solve time.
My visible-only experiment checks all three supplied labels and records its
results under checks/solve-ready-visible.json. This is the first submitted
solution for these final-source bytes; no failed solve was manufactured.

Both query inputs have 5 rows × 14 columns. Output: unknown.
Private query correctness remains withheld for independent scoring.

## Record recovery

A stale earlier-source attempt and finish snapshot reappeared after the initial
archive operation; the finish command refused to overwrite that snapshot. The
mixed record, including this solver's successful visible check, is retained in
checks/solve-reset-failure. I archived that entire folder, prepared the same
deterministic final-source challenge in an empty folder, and checked this same
first-authored solver again. This was an infrastructure recovery, not a failed
solution or an invented negative. The source of the stale-file restoration has
not been established. No reference or private query answer was opened.
