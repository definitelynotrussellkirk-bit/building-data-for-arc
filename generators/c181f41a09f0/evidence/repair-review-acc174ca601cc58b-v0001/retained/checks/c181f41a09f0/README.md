# Bounded peer review — c181f41a09f0

Current source `fdaef0b9eb49b55dd60c29589e8f5fca51519fe52b3357ab2f146234fdd7eba0`
was reviewed with its notes and empty current review index. Production and its
existing parametric proposal were not edited.

The public API materialized four actual default lessons at seed 0. **The default
is four demonstrations and one query**, not three demonstrations obtained by
subtracting a query from `EXAMPLES_NEEDED`. Each lesson therefore teaches all four
horizontal/vertical and low/high source branches. Catalog approval was
`not_reviewed_safe`; the explicit research request `allow_unapproved=True` is
recorded, and no approval state changed.

Six rival programs were executed against every visible demonstration: always
send horizontal blocks low or high; always send vertical blocks low or high;
reverse each copied cap block; retain the unmarked strip. All six were eliminated
by demonstrations in all four lessons. The probe tests query disagreements only
for demonstration-fitting rules, so no rival query execution was warranted.

The public request generated 20 Racket-labeled pairs, and the additional audit
performed 96 protected rival executions. `probe.json` retains source/program
hashes, runtime identity, full canonical/rival programs, actual request, per-lesson
profiles and per-rival demonstration-fit results. No concrete finding was observed.

Reproduce from the outer packet folder, using new output and receipt names:

```bash
WORK/.venv/bin/python review.py run \
  --receipt checks/c181f41a09f0/probe-replay-command.json \
  python3 ../checks/c181f41a09f0/probe.py --count 4 --seed 0 \
  --out ../checks/c181f41a09f0/probe-replay.json
```

Limits: four default lessons and six specific alternatives; no broad battery,
universal uniqueness claim, approval, parametric admission, or training change.
The current notes describe an existing parametric proposal; that proposal was
not newly reviewed or qualified in this production-default probe.
