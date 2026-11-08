# Proposed ray-relation parameter for c5a69e7cd8c8

Status: **proposed / unapproved task-local prototype**. The approved production
`generator.py` remains byte-identical at SHA-256
`132987cd4a2c9f6e2634c8edc5e54db1ff5a493c9a7b3ba6d8c3246150f4b6a0`.
The canonical/default Racket source remains byte-identical at SHA-256
`cd162c43ed682af8c42df94bcb1c099d019115b65f32e70077f02d447664267d`.

## Parameter

`ray_relation` is selected once per episode and stays fixed across every
demonstration and query.

- `opposite_opening` (default): exact canonical behavior. Find the unique-color
  singleton, infer its one open cardinal side, and paint its color through zero
  cells on the opposite ray while preserving occupied cells.
- `through_opening`: keep the same singleton, opening, support, and paint-order
  reasoning, but paint through the open side instead. Its materialized Racket
  source SHA-256 is
  `d4f0f2b1c93e83e8f2a7e02e6ca2f58cc2b82640fd9ff4c9c1371288371ef58e`.

The retained batch uses one shared input seed for both settings, so the visible
inputs are identical and only the rule parameter changes. Each setting has three
demonstrations and four distinct queries. Exact Racket execution labels every
pair; the alternate setting fails the demonstrations and changes every retained
query answer.

## Reproduce

Run from the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/c5a69e7cd8c8/workspace/parametric/prototype.py \
  materialize --seed 17 --demos 3 --queries 4 \
  --out ../checks/parametric/c5a69e7cd8c8-ray-relation-v1

python3 review.py run python3 \
  generators/c5a69e7cd8c8/workspace/parametric/prototype.py \
  verify --out ../checks/parametric/c5a69e7cd8c8-ray-relation-v1

python3 review.py task-tests c5a69e7cd8c8 --phase after \
  --out ../checks/c5a69e7cd8c8-task-tests-final-v3
```

The writer hashes and writes the exact canonical public bytes, separates hidden
settings/programs/query labels under `private/`, sorts by public ID, and rejects
duplicate visible payloads or ID collisions before emitting files. The verifier
rechecks source bindings, manifest hashes, canonical public bytes, public/private
projection, hidden-pair consistency, unique two-setting coverage, confined report
paths, report schema/source/approval/count contracts, exact Racket semantics, and
demonstration-only rival rejection.

## Scope and limits

This evidence covers the two declared settings and two materialized episodes.
It does not prove identifiability against every possible ARC hypothesis, approve
the prototype, modify the fixed canonical production path, refresh approval
hashes, or admit examples to training. Demo/query counts are independently
configurable from 1 through 12; the retained acceptance-oriented evidence uses
3 demonstrations and 4 queries.
