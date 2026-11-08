# Blind solve work log

## Exposure and materials

This solve used only the visible examples printed by `blind prepare`,
`solve-blind/README.md`, `solve-blind/challenge.json`, and my own Python
experiments on that challenge. I have no earlier rule exposure. I did not
consult any generator source, canonical catalog, rule, reference solution,
private answer, other solution, or prior solution notes. I wrote only
`solve-blind/solution.py` and this work log; the supplied harness manages its
own evidence.

## Visible evidence

- Train 0: Input 9 rows × 10 columns. Output 9 rows × 10 columns.
  The full color-9 row is at zero-based row 4. Every row maps to row `8 - r`.
- Train 1: Input 15 rows × 13 columns. Output 15 rows × 13 columns.
  The full color-9 row is at zero-based row 8. Colored cells map to row
  `16 - r`, preserving columns. This supports reflection around the line,
  rather than simply reversing all rows around the grid's middle.
- Train 2: Input 12 rows × 12 columns. Output 12 rows × 12 columns.
  The full color-9 row is at zero-based row 6. Rows map to `12 - r`.
  The three color-6 cells on source row 0 would land on row 12, outside
  the output, and are absent. The other two color-6 cells land on row 11.
  This supports clipping at the original grid boundary.
- Query 0: Input 8 rows × 9 columns. Output unknown.
- Query 1: Input 15 rows × 12 columns. Output unknown.

## Hypothesis and experiment

The color-9 horizontal line is a mirror axis. Reflect the whole grid across
that row, keep the original dimensions, and discard destinations outside
the grid. A cell at `(r, c)` maps to `(2 * axis - r, c)`. The line maps to
itself. Unfilled locations are background color 0.

Before writing the solution, I ran a Python experiment that read only
`challenge.json`, found the unique full color-9 row in each training input,
applied this mapping, and compared every visible output cell. It reported
zero mismatches on all three training examples. It also counted zero
clipped nonzero cells in examples 0 and 1 and three in example 2.
The experiment exited with code 0 and did not inspect private query labels.

## Implementation and checking

Solver revision 1 implements the reflection directly. It requires the
single full horizontal color-9 row supported by every visible input.
There were no failed hypotheses implemented and no failed solver revisions
at the time this log was frozen. No failures have been fabricated.

The official check for this revision is:

```sh
python3 solve_episode.py blind check --intent solve --note 'Revision 1: reflect across the unique full horizontal color-9 row, preserve dimensions, and clip out-of-bounds destinations; the visible-data experiment matched all three training outputs.'
```

The harness records the check's result separately when it freezes this
code and log. If all visible examples match and the queries execute, I
will stop: the supported transformation is simple and no additional
revision is justified by the visible evidence. Private query correctness
remains unknown during this solve. The solution does not claim to cover
unseen vertical axes, different axis colors, or ambiguous multiple lines.
