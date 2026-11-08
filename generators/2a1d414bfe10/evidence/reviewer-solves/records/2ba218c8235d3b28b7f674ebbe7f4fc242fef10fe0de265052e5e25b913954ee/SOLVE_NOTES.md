# Visible-only solve notes

## Scope and exposure

This isolated solver began without exposure to the transformation rule. I read
only this folder's README.md, challenge.json, and placeholder solution.py, then
my own experiment results and work. I did not consult generator source,
canonical data, Racket/reference solutions, private labels, previous solve
folders, or other agents' notes.

The parent review had earlier rule exposure. Therefore the episode must record
`--earlier-exposure yes` at review level and `--reference-consulted no` for this
solve. Isolation does not erase the review's earlier exposure.

## Hypothesis 1

Group nonzero cells by their color. Independently translate each colored shape
so its bounding box begins at row 0, column 0, without rotation or reflection.
Overlay those shapes and retain positions occupied by exactly two colors.
Render retained positions as 8 and all other positions as 0, then crop to the
smallest bounding rectangle containing the retained positions.

The three visible examples have one shape in each of colors 1, 2, and 3. The
code groups by any nonzero color, which is a natural extension but not separately
established by these examples. No visible example has an empty double-coverage
set; the code returns [[0]] in that unobserved case.

## Visible evidence and exploration

I ran one independent Python calculation directly from challenge.json. The
calculation was saved in visible_experiment.json and exited 0. It computed the
normalized shapes and positions of exact double coverage, then compared its
cropped output with every provided training output:

| Example | Exact double-coverage coordinates before crop | Predicted output | Match |
| --- | --- | --- | --- |
| 0 | (0, 2), (1, 1) | [[0, 8], [8, 0]] | Yes |
| 1 | (0, 1), (1, 3) | [[8, 0, 0], [0, 0, 8]] | Yes |
| 2 | (0, 0) | [[8]] | Yes |

These examples also explain why cells with triple coverage are excluded.
Example 0 contributes a cell shared by colors 1 and 2 and another shared by
colors 1 and 3; example 1 contributes cells shared by colors 2 and 3. The rule
therefore treats every pair alike. Different cropped dimensions follow from
the retained positions instead of from the original canvas or shape extents.

## Implementation and recorded attempt

I replaced the placeholder with the direct counting-and-cropping implementation
of Hypothesis 1. No failed implementation or hypothesis was invented, and no
earlier attempt was deleted. This is the first solver revision submitted to the
episode checker.

The intended check is, from the packet root:

```sh
python3 review.py solve check --intent solve --note 'Hypothesis 1: align each nonzero color shape at its bounding-box top-left, retain exactly two-shape coverage as 8, and crop; an independent calculation reproduced all three visible training outputs.'
```

Feedback is limited to visible examples and execution. I have not seen hidden
query outputs and will not claim hidden-query correctness. The stopping
criterion is successful execution and a match on all visible examples for this
coherent rule; any reported hidden query predictions remain unverified.


## Recovery and duplicate validation

The first isolated-solver check completed with all 3 visible examples matching,
and the wrapper labeled that preserved check revision 2. The subsequent finish
command exited 1 because FINISHED_NOTES.md already existed. I did not open or
modify that preexisting snapshot. My own original check output and finish-error
record are preserved in ISOLATED_SOLVER_RESULTS.json and in the retained prior
public directory.

The parent review reported that it archived the complete mixed prior public
directory, removed stale active records, and prepared the same final generator
hash and a byte-identical public challenge with zero active attempts. I restored
only my own solution.py, SOLVE_NOTES.md, visible_experiment.json, and
ISOLATED_SOLVER_RESULTS.json from the archive. I did not read its old finish
snapshot, old attempts, references, generator, private labels, or any other
solver's notes.

The next check submits the same unchanged candidate again after this recording
cleanup. It is duplicate validation of the same inference attempt, not a new
inference attempt or a natural solver failure. Earlier successful check and
finish-error records remain retained. Review-level earlier exposure remains yes;
reference consultation by this isolated solver remains no. The check can assess
visible examples and execution only; hidden-query correctness remains unknown.
