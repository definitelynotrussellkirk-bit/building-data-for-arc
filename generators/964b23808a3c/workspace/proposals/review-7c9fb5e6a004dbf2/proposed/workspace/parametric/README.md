# Proposed column-selector × segment-owner family

This is a **task-local prototype**, separate from canonical execution. It does
not alter the selected Racket authority, rule hash `c7e69da25375`, canonical
labels, or production generator dispatch.

The family preserves the original reasoning sequence: find the nonzero markers
in each column, decide whether color 5 makes that column active, order the
markers from top to bottom, and paint the intervals those markers delimit.

| Parameter | Values | Canonical/default | Meaning |
| --- | --- | --- | --- |
| `selector_mode` | `ends_in_5`, `contains_5` | `ends_in_5` | Activate only columns whose last marker is 5, or any column containing 5. |
| `segment_mode` | `current`, `previous` | `current` | Give each interval the lower/current marker's color, or the preceding marker's color while preserving the current marker cell. |

A complete setting is chosen once per episode as `ALL_SETTINGS[seed % 4]` and
held fixed for all three demonstrations and the query. The episode uses the
parent generator's four deterministic profiles in order: minimal, clean, noisy,
dense. The noisy demonstration contains both an internal-5 distractor and
multi-marker targets, so it separates all four settings; the dense query does
the same independently.

`prototype.py` executes every label with the exact instantiated Racket program
through `RacketBridge`; its Python transform is only a parity assertion. The
canonical/default program is byte-for-byte identical to the selected authority.
The four materialized programs live in `rules/`. Public episode files contain
only three labelled demonstrations and one unlabelled query; parameters,
program text, rival outputs, and the query answer remain private evidence.

From the outer packet directory, create retained evidence with:

```bash
python3 review.py run python3 \
  generators/964b23808a3c/workspace/parametric/prototype.py \
  --seed 17 \
  --out ../checks/parametric/selector-segment-seed17
```

Focused tests:

```bash
python3 review.py run python3 -m arcpuzzles check 964b23808a3c \
  --stage task_tests --phase after --out ../checks/task-tests
```

The retained seed-17 evidence is a bounded authoring result, not approval for
training admission. It distinguishes the four declared settings only; it does
not prove uniqueness against arbitrary programs, and broader seed coverage
would be required before promoting the family into a production API.
