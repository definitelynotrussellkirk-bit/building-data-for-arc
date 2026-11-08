# Workspace

The selected implementation is `../generator.py`.  Workspace probes are review
aids and are never automatically selected.

## Lesson probe

`lesson_probe.py` imports the selected generator and records:

- canonical fit for every declared `CANONICAL_SHORTCUTS` rival;
- generated counterexamples for every `LESSON_COMPETITORS` rival;
- all three-of-four query rotations over consecutive schedule starts;
- strict-canonical coverage, witness frequency, and unique-input counts;
- all 24 exact joint boundary override cases.

Run from the repository root:

```bash
python3 generators/d5d9fdb01bdd/workspace/lesson_probe.py \
  --windows-per-band 100 \
  --out ../checks/d5d9fdb01bdd-lesson-probe.json
```

The probe uses the Python mirror only after the normal Racket rule-smoke stage
has established parity.  Its JSON report hashes the imported generator and
states the finite-domain limitations explicitly.
