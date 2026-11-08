# Episode-fixed panel threshold — proposed prototype

This task-local authoring tool varies one hidden rule parameter while preserving
the canonical task's complete reasoning structure: find the two divider rows and
columns, count color-6 cells in each of the nine panels, and emit a 3×3 mask.

| `panel_threshold` | Executed rule | Status |
| --- | --- | --- |
| `1` | output `1` iff a panel contains at least one color-6 cell | proposed |
| `2` | output `1` iff a panel contains at least two color-6 cells | canonical/default |
| `3` | output `1` iff a panel contains at least three color-6 cells | proposed |

The selected production generator and its approved threshold-2 rule are not
modified. The prototype pins the exact selected generator and canonical Racket
source hashes, materializes one exact Racket program per threshold, and executes
all selected and rival labels through the bundled Racket bridge. Every sampled
input uses a declared production count profile containing panel counts 1, 2, and
3, so each demonstration independently distinguishes all three thresholds.

One threshold is chosen from the episode seed (or explicitly supplied) and remains
fixed across all demonstrations and queries. Demonstration and query counts are
independent. Public challenges contain labeled demonstrations and unlabeled query
inputs only; their opaque IDs are derived solely from those visible bytes.

Run from the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/a9c4475d7cda/workspace/parametric/prototype.py \
  --seeds 0 1 2 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/a9c4475d7cda-panel-threshold-v1

python3 review.py run python3 -m pytest -q \
  generators/a9c4475d7cda/tests/test_parametric_threshold.py
```

The evidence command writes three complete private episodes, visible-content
hash-named public challenges, the exact `.rkt` programs, source snapshots, hashes,
runtime identity, canonical threshold-2 replay, and demonstration-only finite-rival
certificates. It refuses to overwrite an existing destination.

This is a **proposed, unapproved prototype**. Its finite evidence covers only the
declared thresholds and retained seeds. It does not alter canonical approval,
admit data to training, or establish learning benefit.
