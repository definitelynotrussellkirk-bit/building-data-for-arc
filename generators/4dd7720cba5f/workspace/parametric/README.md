# Proposed `destination_scope` episode prototype

This task-local prototype adds one hidden, episode-fixed rule parameter without
changing the selected production generator or canonical authority.

## Contract

| Field | Value |
|---|---|
| Parameter | `destination_scope` |
| Allowed settings | `all_tiles`, `empty_tiles_only` |
| Canonical/default | `all_tiles` |
| Demonstrations | 3 by default, independently configurable |
| Queries | 4 by default, independently configurable |
| Status | proposed and unapproved |

Both settings parse the same zero-separated 5×5 framed tiles, group them by
frame color, and compute the union of same-color motif offsets.
`all_tiles` writes the union into every same-color tile and is byte-for-byte the
canonical Racket rule. `empty_tiles_only` writes the same union only into tiles
whose input interior is empty, leaving partially occupied source tiles partial.

Retained inputs use the production generator's lawful multi-source union
profiles. This constraint is deliberate: each pair must make the two settings
produce different outputs. One setting is selected from the deterministic
**episode seed** and is held fixed across every demonstration and query.

## Exact four-query evidence command

From the outer extracted packet directory:

```bash
python3 review.py setup
python3 review.py run python3 \
  generators/4dd7720cba5f/workspace/parametric/prototype.py \
  --seeds 0 2 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/destination-scope-v1
```

The writer refuses to overwrite an existing output directory. Seeds `0` and `2`
cover the two settings in this version. The retained run produced two complete
episodes, 3 demonstrations and 4 distinct queries per episode, and 28 protected
Racket executions (selected plus rival on all 14 pairs).

## Output boundary

- `public/challenge-<opaque-id>.json`: demonstration inputs/outputs and query
  inputs only.
- `private/episode-<opaque-id>.json`: setting, seed, query labels, predictions,
  hashes, and verification metadata.
- `private/rules/*.rkt`: exact materialized programs for both settings.
- `private/distinguishing_witness.json`: one lawful input with both Racket
  outputs.
- `report.json`: bounded aggregate receipt and limitations.

Each public ID is the SHA-256 of the exact visible challenge bytes. It does not
encode the seed, setting, setting ordinal, hidden query outputs, or rule text.
The tests explicitly verify that mutating private metadata and query labels does
not change the public ID.

## Verification

```bash
python3 review.py run python3 -m pytest -q \
  generators/4dd7720cba5f/tests/test_parametric_destination_scope.py

python3 review.py check --stage task_tests --phase after --timeout 600 \
  --out ../checks/parametric/task-tests-v1
```

The second command is the portable staged route for the complete task test
folder. Directly invoking the legacy production tests from the projected repo
without staging does not install the expected
`puzzle_generators/per_puzzle/<id>/` runtime import path.

## Limits

This is finite evidence for two settings and two retained seeds, not proof that
these are the only plausible rules. It does not modify `generator.py`, canonical
data, approval records, or production APIs, and it grants no training admission.
