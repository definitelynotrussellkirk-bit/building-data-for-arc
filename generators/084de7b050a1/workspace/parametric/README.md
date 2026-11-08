# Proposed `axis_priority` rule parameter

This task-local prototype varies one executed rule choice while preserving the
canonical family: when a colored dot shares **both** a column and a row with blue
cells, should the column-aligned reflection or row-aligned reflection win?

| value | meaning | status |
|---|---|---|
| `column_first` | evaluate the same-column blue anchor first | canonical default |
| `row_first` | evaluate the same-row blue anchor first | proposed alternative |

The value is chosen once per episode. It is never resampled per pair. An episode
must contain a both-aligned witness in its demonstrations before a query whose
answer depends on the same choice. The retained Racket programs are complete and
runnable; `column_first.rkt` must retain normalized hash `e059ff61aa1e`.

From the packet root, execute both rules and rebuild the retained episodes with:

```sh
python3 review.py run python3 \
  generators/084de7b050a1/workspace/parametric/axis_priority.py \
  --out ../checks/parametric/axis-priority-evidence.json
```

The command writes full source-bound execution evidence under `WORK/checks/` and
refreshes `examples.json` beside this README. It requires the bundled Racket
runtime selected by `review.py run`; there is no Python-only success fallback.

This is a **proposed prototype**, not a selected generator change, a canonical
rule edit, or an approved production parametric interface. It changes only axis
precedence. First-anchor selection, dot order, clipping, overwrite semantics,
colors, and input sampling stay fixed.
