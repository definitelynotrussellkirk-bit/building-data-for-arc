# Workspace

`lesson_probe.py` is the retained source-bound curriculum probe for the selected
`../generator.py`.

Run from the packet repository through the Racket wrapper:

```bash
python3 run_with_racket.py python3 \
  generators/b2d6e6b60917/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/lesson-probe-100.json
```

The probe:

- checks the Python mirror on every canonical pair;
- verifies every declared canonical shortcut against those pairs;
- samples disjoint three-demo-plus-query lessons in all difficulty bands;
- iterates the generator's live schedule, witnesses, and competitors;
- records unique inputs, witness hits, rival disagreements, survivors, and
  lesson-identifiability failures; and
- binds the report to the generator SHA-256 and canonical `RULE_HASH`.

Its labels come from `rule_mirror` after canonical parity is established. The
central `rule_smoke` and `semantic_gate` stages remain the authoritative Racket
execution checks.
