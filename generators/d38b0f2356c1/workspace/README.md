# Task-local review tools — d38b0f2356c1

`semantic_probe.py` is a source-bound finite lesson audit, not an alternate
label authority. It loads the selected generator, enumerates the executable
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`
declarations, verifies that claimed canonical shortcuts fit every public pair,
and samples deterministic three-demo lessons at all cyclic schedule starts.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 -B \
  generators/d38b0f2356c1/workspace/semantic_probe.py \
  --lessons-per-band 100 \
  --out ../checks/semantic-probe-100.json
```

For lesson `i`, the probe uses seed `1009+i`, start index `i mod 3`, three
consecutive demonstrations, and the next generated input as a query. It crosses
that schedule with easy, medium, and hard. The report includes exact rival
disagreements, witness coverage, unique-input counts, deterministic replay,
source hashes, and limits. It does **not** claim universal induction or learner
success. Canonical and repository Racket gates remain the rule authority.
