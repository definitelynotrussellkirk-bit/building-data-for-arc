# Workspace tools for fa55db418c9d

The selected implementation is `../generator.py`. These tools are not selected as runtime generators.

## `curriculum_probe.py`

Runs a source-bound, actual-Racket census over linked lessons. It uses the generator’s live `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and schedule declarations; checks canonical outputs; labels every generated grid with canonical Racket; verifies the Python mirror; tests all schedule residues induced by the sampler; and saves an exact shortcut witness.

From the review packet root:

```bash
python3 run_with_racket.py python3 \
  generators/fa55db418c9d/workspace/curriculum_probe.py \
  --lessons-per-band 100 \
  --out ../checks/curriculum-probe-final-v301.json
```

The final sampler uses 100 lessons per band, five demos plus one query, start index `11 * lesson_index`, and a SHA-256-derived seed recorded in the JSON. The report is a finite measured census, not universal induction evidence.

## `audit_probe.py`

Reproduces the two immutable adversarial audits without editing either target. It records exact generator/rule hashes, checks published canonical outputs with actual Racket, measures override behavior, and saves a default-generated disconnected-template counterexample with actual and documented-rule outputs.

```bash
python3 run_with_racket.py python3 \
  generators/fa55db418c9d/workspace/audit_probe.py \
  --out ../checks/audit-probe-final.json
```

## Focused tests

From the packet root:

```bash
PYTHONPATH=repo/shared/runtime pytest -q \
  repo/generators/fa55db418c9d/tests/test_generator_fa55db418c9d.py \
  repo/generators/fa55db418c9d/tests/test_audit_probe.py
```
