# Parametric empty-line paint color — proposed prototype

This task-local prototype varies one episode-level rule parameter while preserving
the original reasoning path: find every row and column consisting entirely of
background zero, then repaint the union while preserving all other cells.

| Parameter | Allowed values | Canonical/default |
| --- | --- | --- |
| `paint_color` | `2`, `6` | `2` |

The setting is chosen once per episode and held fixed across three demonstrations
and four distinct queries. Each complete two-color input group uses the same
inputs, and the evidence writer can retain multiple independent paired groups.
Demonstrations
include a both-axis case, a columns-only case, and a rows-only case, so they refute
the other color as well as row-only and column-only shortcut rules before any
query is answered. Exact instantiated Racket programs produce selected labels and
all declared rival predictions. The canonical setting returns the selected
canonical program byte-for-byte.

Run from the outer packet directory:

```sh
python3 review.py run python3 generators/548c1010ce89/workspace/parametric/prototype.py \
  --out ../checks/parametric/paint-color
python3 review.py task-tests 548c1010ce89 --phase after --out ../checks/task-tests
```

Public challenge files contain only demonstration inputs/outputs and query inputs;
their filenames are hashes of those exact visible bytes. Private files retain the
fixed setting, four query answers, exact Racket source/hashes, and rival receipts.
This is a proposed prototype only: it does not change the canonical rule, grant
variant approval, or admit episodes to training.

Limits: two paint colors, the retained seed groups named in each report, three
named rival families, and a controlled seven-profile episode. Finite evidence
does not establish uniqueness against arbitrary programs or arbitrary-seed
coverage.
