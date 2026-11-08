# 4c17a205be08 review workspace

`audit_curriculum.py` is a reusable, deterministic probe for this generator. It checks canonical shortcut fit, generated shortcut counterexamples, transform/palette/component coverage, strict validation, and every scheduled five-demo lesson window.

From `repo/`:

```bash
python3 generators/4c17a205be08/workspace/audit_curriculum.py \
  --seed 20261002 --samples 24 \
  --out ../checks/final-curriculum-audit.json
```

The report uses the generator's Python mirror for fast diagnostics. Treat the selected Racket program as authoritative and pair this report with `rule_smoke`, `semantic_gate`, or a protected-Racket counterexample probe before making output claims.
