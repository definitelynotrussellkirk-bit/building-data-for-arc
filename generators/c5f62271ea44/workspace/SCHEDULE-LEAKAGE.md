# Check whether the schedule reveals the query

`check_schedule_leakage.py` is a reusable, source-bound authoring probe for this
family. It gives a hypothetical lookup the known query position, all four exact
ordered demonstration transforms, and the query's actual blue source/target
corner positions. It then searches for two generated queries with that same
information but different required transforms. Such a collision shows that this
lookup cannot always replace reading the other three query marker colors.

Run from the outer packet directory, using a new output path:

```bash
python3 review.py run ../.venv/bin/python generators/c5f62271ea44/workspace/check_schedule_leakage.py --seed-count 256 --out ../checks/my-schedule-leakage
python3 review.py run ../.venv/bin/python -m arcpuzzles apply c5f62271ea44 --input ../checks/my-schedule-leakage/witness-inputs.json --out ../checks/my-schedule-leakage/racket.json
```

The first command executes the selected generator through `reviewer_support`.
It checks each generated query's grammar and observed transform, records the
generator/probe hashes, and retains a pair of exact seed/start/index witnesses
for each holdout position with a collision. It intentionally does not label
outputs. The second command obtains actual canonical Racket outputs for the ten
retained witness inputs. The final review includes an independent verification
script in `checks/schedule-leakage-v3-3/verify.py` checking those outputs and the
shared projections.

The retained v3.3.0 run used seeds 0..255, all 16 starting residues, and all five
known holdout positions. It generated 5,120 inputs and examined 4,096 schedule
windows / 20,480 holdout events. Those are not 20,480 distinct Racket-labeled
lessons: windows share queries, and only the ten collision witness inputs were
subsequently labeled by this probe's Racket check. Separate production and
fixed-seed lesson censuses supply full materialized lesson evidence.

The lookup was refuted at every holdout position in this bounded cohort. This
does not establish that every query needs every marker, that no other information
leaks through the schedule, or that a model cannot exploit partial correlations.
The fraction of observations in colliding keys is an observed lower bound on
ambiguity of this projection in the sampled support. Keys observed only once
are not evidence of a reliable predictor. These distinctions matter when a
small, heavily structured teaching curriculum is used to assess generalization.
