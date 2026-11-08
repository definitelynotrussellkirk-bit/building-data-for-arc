# Proposed `floor_acceptance` rule parameter

This directory is a **task-local, unapproved prototype**. It leaves the selected
production generator, canonical labels, canonical Racket authority, `RULE_HASH`,
and approval state unchanged.

## Parameter

`floor_acceptance` is selected once from the episode seed and remains fixed
across every demonstration and query.

| Value | Containment test | Role |
| --- | --- | --- |
| `whole_section` | accept the first candidate only when every cell of its floor is red | Canonical/default |
| `under_drop` | accept the first candidate when the floor cell directly under the blue drop is red | Proposed alternative |

Both settings preserve the original reasoning structure: remove the blue drop,
follow its column through vertically ordered red open-top sections, choose the
first section that satisfies the fixed episode-level containment test, fill that
section, and otherwise spill across the bottom row. Only the floor-acceptance
predicate changes. Input constraints do not depend on the hidden setting.

The prototype deliberately generates lawful `second` and `bottom` scenes with a
floor gap away from the drop column while the floor cell under the drop remains
red. Thus every retained input distinguishes the two settings without a reskin
or parameter-specific input cue. Each retained episode has three labeled
demonstrations and four distinct unlabeled queries. Every label is produced by
executing the matching exact Racket program, and every query is checked against
the other setting using only the three demonstrations.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/52ac31926856/workspace/parametric/prototype.py materialize \
  --seed 0 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/floor-acceptance-v1

python3 review.py run python3 \
  generators/52ac31926856/workspace/parametric/prototype.py verify \
  --out ../checks/parametric/floor-acceptance-v1

python3 review.py check --stage task_tests --phase after --timeout 600 \
  --out ../checks/task-tests-floor-acceptance-v2
```

Focused portable tests are in
`generators/52ac31926856/tests/test_parametric_floor_acceptance.py`.

## Public projection

Public files contain only demonstration inputs/outputs and query inputs. A batch
is sorted by public ID before writing and duplicate visible payloads are rejected.
Their opaque `challenge-<sha256>.json` names are derived by
`reviewer_support.public_challenge_bytes` and `public_challenge_id`; private-only
metadata (seed, setting label, Racket source, and hidden query answers) cannot
change a public name unless the visible demonstrations or query inputs also change.
Private episodes retain setting maps, exact Racket source/hashes, query answers,
and rival analysis separately.

## Limits

The retained evidence covers two declared settings, two consecutive seeds,
three demonstrations, four queries per episode, and the one alternate setting
as a declared rival. It does not establish uniqueness against undeclared rules,
create a production parametric API, change canonical authority, approve either
variant, or admit generated data to training.
