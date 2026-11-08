# Proposed source-rotation parameter

**Status: proposed, unapproved prototype.** This task-local authoring tool does
not change the selected generator, canonical Racket authority, rule hash,
approval state, or production generation API.

## Parameter contract

| Property | Contract |
| --- | --- |
| Parameter | `source_rotation_quarter_turns` |
| Allowed values | `0`, `1`, `2`, `3` clockwise quarter-turns |
| Original/default | `0`; its Racket source is byte-for-byte the selected canonical program |
| Episode choice | `ALLOWED_QUARTER_TURNS[seed % 4]`, once before all demonstrations and the query |
| Invariant reasoning | Read the same fixed 2×2 source block, transform its orientation, scatter its four values to the output corners, clear every other output cell |
| Demonstrations/query | Three demonstrations and one query |
| Input witnesses | 4×4 canonical anchor, 4×4 corner decoys, 6×6 source halo, 7×5 edge midpoints |

A clockwise turn rotates the extracted source block before corner placement. For
source `[[a,b],[c,d]]`, the four corner orders are:

- `0`: `[[a,b],[c,d]]` (canonical)
- `1`: `[[c,a],[d,b]]`
- `2`: `[[d,c],[b,a]]`
- `3`: `[[b,d],[a,c]]`

Every prototype input uses four pairwise-distinct source colors, so each
labelled demonstration distinguishes the chosen setting from all three declared
parameter rivals. Consecutive seeds `0..3` share the same four inputs and vary
only the hidden rule, making the setting-difference evidence direct.

## Run Racket-backed evidence

From the outer extracted packet directory:

```bash
python3 review.py run python3 generators/144582f287b5/workspace/parametric/prototype.py \
  --seeds 0 1 2 3 \
  --out ../checks/parametric/corner-rotation
```

Equivalent command from `WORK/`:

```bash
python3 run_with_racket.py python3 \
  generators/144582f287b5/workspace/parametric/prototype.py \
  --seeds 0 1 2 3 \
  --out ../checks/parametric/corner-rotation
```

The destination must not already exist. The run writes all four exact `.rkt`
programs, canonical-default checks, a setting-difference witness, private
answer-bearing episodes, public answer-masked challenges, hashes, runtime
identity, and `report.json`. All labels are obtained by executing the
materialized Racket program through the bundled bridge; the Python implementation
is only an independent cross-check.

## Focused tests

The task-test gate collects `tests/test_parametric_corner_rotation.py`. From the
outer packet directory:

```bash
python3 review.py run python3 -m arcpuzzles check 144582f287b5 \
  --stage task_tests --timeout 600 --phase after \
  --out ../checks/task-tests
```

The tests pin the canonical source hash, execute all four settings with real
Racket, verify complete episodes and rival refutations, check public masking,
and exercise the evidence writer.

## Limits

This is finite authoring evidence, not a proof of universal identifiability.
Repeated source colors, translated source blocks, arbitrary decoy layouts, and
non-corner scatter targets are outside the prototype sampler. Only the four
quarter-turn settings are treated as parameter rivals. Integration into any
shared production parametric API would require a separate review.
