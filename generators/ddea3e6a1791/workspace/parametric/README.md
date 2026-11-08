# Proposed episode-level `background_color` parameter

This is a **prototype**, not part of the selected canonical generator or its
approval path. The core transformation stays fixed: crop to the tight bounding
box of every cell that is not the episode background.

| value | foreground predicate | status |
|---|---|---|
| `0` | cell value is nonzero | canonical/default |
| `9` | cell value is not 9 | proposed alternative |

The value is selected once per episode and shared by all three demonstrations
and the query. For `9`, canonical inputs are transformed by swapping colors 0
and 9, preserving geometry while allowing 0 to be foreground. Every retained
demonstration distinguishes the settings: the wrong predicate treats the
selected canvas color as foreground and returns the full input rather than the
compact crop. Public challenges omit the parameter, Racket source, and query
answer.

From the packet root, verify both settings with the protected Racket runtime:

```bash
python3 review.py run python3 \
  generators/ddea3e6a1791/workspace/parametric/verify.py \
  --seed 20261019 \
  --out ../checks/parametric/report.json \
  --artifact-dir generators/ddea3e6a1791/workspace/parametric/materialized
```

The report records exact Racket programs and hashes, selected generator bytes,
runtime identity, eight Racket-checked pairs, six distinguishing training pairs,
and one explicit same-input disagreement. The default program is checked
against the canonical program’s normalized hash. This finite two-setting probe
does not approve a production parametric API or establish uniqueness against
undeclared hypotheses.
