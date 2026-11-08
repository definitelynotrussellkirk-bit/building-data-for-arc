# Proposed `priority_order` rule parameter

This directory is a **task-local, unapproved prototype**. It leaves the selected
production generator, canonical labels, canonical Racket authority, and
`RULE_HASH` unchanged.

## Parameter

`priority_order` is selected once from the episode seed and is fixed across
every demonstration and query.

| Value | Effective panel priority | Role |
| --- | --- | --- |
| `q1_q2_q3` | `Q1 > Q2 > Q3` | Canonical/default |
| `q1_q3_q2` | `Q1 > Q3 > Q2` | Proposed alternative |

Both settings preserve the original reasoning structure: split the 4x14 input
into three aligned 4x4 panels around the two divider columns, overlay
corresponding cells, and emit the first nonzero role color under one fixed
priority. Only the order of the two lower-priority panels changes.

Prototype inputs are drawn from the generator's lawful `generalized` family.
Every input contains all eight panel-occupancy states, including a cell where Q2
and Q3 overlap while Q1 is absent, so the two settings necessarily make a
different prediction without changing the input manifold.

Each retained episode has two labeled demonstrations and four distinct unlabeled
queries. Every label and counterfactual is produced by executing the matching
exact Racket program. Each query is checked independently against the other
declared setting using only the two demonstrations. Public files contain only
visible demonstrations and query inputs; filenames are SHA-256 hashes of the
exact visible bytes written, independent of seeds, parameter names, Racket
source, and query answers. Before any output tree is created, the writer plans
the complete public batch, rejects duplicate visible payloads or ID collisions,
and sorts writes by public ID. Private episode files remain in episode order and
record their corresponding public path explicitly.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/2534c7164e36/workspace/parametric/prototype.py materialize \
  --seed 0 --demo-count 2 --query-count 4 \
  --out ../checks/parametric/2534-priority-order-public-batch-v2

python3 review.py run python3 \
  generators/2534c7164e36/workspace/parametric/prototype.py verify \
  --out ../checks/parametric/2534-priority-order-public-batch-v2
```

Focused portable tests are under
`generators/2534c7164e36/tests/test_parametric_priority_order.py`.

## Limits

The retained evidence covers the two declared settings and two consecutive
seeds. It checks one declared rival per episode, not all possible rules. It does
not add a production parametric API, refresh the canonical authority, approve a
variant, or admit any generated episode to training.
