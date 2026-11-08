# Reviewer workspace for 7a6e065e8273

The selected implementation is `../generator.py`. These tools are supplementary audits; the selected canonical Racket rule remains the label authority.

## `reference_probe.py`

An independent literal geometry oracle, distribution probe, and optional real-Racket parity check. It does not import the generator's transformation helpers.

```bash
python3 run_with_racket.py python3 \
  generators/7a6e065e8273/workspace/reference_probe.py \
  --count 500 --racket \
  --out ../checks/7a6e065e8273-independent.json
```

The final review exercised 500 draws in each of `None`, `easy`, `medium`, and `hard`, then compared 67 inputs with the selected Racket rule.

## `lesson_rotation_probe.py`

Reuses source-bound lesson-census JSON and checks every pair as the query. For each rotation it removes that pair from the demonstrations and evaluates the generator's live `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; no rival names are copied into the tool.

```bash
python3 generators/7a6e065e8273/workspace/lesson_rotation_probe.py \
  --census ../checks/lesson-census-easy.json \
  --census ../checks/lesson-census-medium.json \
  --census ../checks/lesson-census-hard.json \
  --out ../checks/lesson-rotation.json
```

The probe verifies every census file is bound to the generator bytes under test. Its result is a finite declared-rival check, not a proof of universal induction.
