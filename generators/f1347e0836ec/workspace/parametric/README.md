# Trigger-diagonal parametric prototype

Status: **isolated proposed prototype; not an approved production rule API**.

This extension preserves the original one-dot objects, vertical paint line, and opposite-corner arms. It varies one episode-level rule parameter:

- `trigger_diagonal="main"` (canonical/default): the top-right/bottom-left orientation is selected when `dot_row == dot_col`.
- `trigger_diagonal="anti"`: the same orientation is selected when `dot_row + dot_col == width - 1`.

The setting is chosen once from the deterministic episode seed and reused for three demonstrations plus one query. The selected canonical generator is used only to sample lawful inputs. Every retained label is produced by executing the exact materialized Racket lambda through the included protected bridge; the alternative lambda is executed against demonstrations to check identifiability.

## Run

From the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/f1347e0836ec/workspace/parametric/build_prototype.py \
  --out-dir ../checks/parametric/f1347-trigger-diagonal-v1
```

The output directory must not already exist. It contains:

- `program-main.rkt` and `program-anti.rkt`, with hashes in `receipt.json`;
- one private complete episode and one solver-safe public challenge per setting;
- exact canonical-default parity over every labeled canonical pair;
- a lawful input separating the settings;
- a deliberate one-example ambiguity where the dot lies on both diagonals;
- source hashes, command receipt, limitations, and aggregate `summary.json`.

Focused tests:

```sh
python3 review.py run python3 -m pytest -q \
  generators/f1347e0836ec/tests/test_parametric_trigger_diagonal.py
```

## Boundaries

The prototype does not edit the canonical Racket source, `RULE_HASH`, selected generator rule, catalog approval, or ordinary production sampler. Evidence covers exactly two settings and finite deterministic episodes. It establishes execution parity and declared-rival identification for those retained cases, not universal identifiability over all lawful grids or all possible nearby rules.
