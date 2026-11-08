# Reviewer workspace for `4b8e135e77e3`

`reference_probe.py` is a reusable independent row-major oracle and distribution audit. It:

- validates canonical examples with an implementation separate from the generator;
- samples all difficulty bands for determinism, validity, transformation strength, profile coverage, and distinct inputs;
- iterates the generator's actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS` declarations rather than maintaining a copied rival list;
- checks the direct prefix/color shortcuts and the cross-axis conditional shortcuts independently; and
- with `--racket`, requires real canonical-authority parity and never falls back to Python.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/4b8e135e77e3/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/independent-audit.json
```

The task-local tests import this tool through `GENERATOR_UNDER_TEST`, so the portable `task_tests` stage exercises the exact staged generator bytes.
