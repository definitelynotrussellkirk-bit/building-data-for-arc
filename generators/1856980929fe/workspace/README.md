# Review workspace: 1856980929fe

`review_probe.py` is a source-bound curriculum probe for the repaired generator.
It reads the sibling `generator.py`, discovers the generator's declared
`LESSON_COMPETITORS` and `SEMANTIC_WITNESSES`, and assembles shared-seed,
consecutive-index lessons.  The JSON report records unique inputs, domain
coverage, schedule coverage, witness hits, per-rival disagreements, and any
rival that fits every demo but changes the query.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/1856980929fe/workspace/review_probe.py \
  --lessons-per-band 100 --demos 5 \
  --out ../checks/analysis/1856980929fe_curriculum_probe.json
```

A nonzero exit means either a generated input failed `self_check` or a declared
competitor survived every demo and changed a query answer.  The probe uses the
Python rule mirror; repository `rule_smoke` and `semantic_gate` provide the
separate source-bound Racket parity evidence.
