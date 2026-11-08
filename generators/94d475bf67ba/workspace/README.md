# Reviewer workspace for `94d475bf67ba`

`reference_probe.py` is an independent geometry parser/oracle and reproducible sampler audit. It is reviewer tooling, not label authority; requested `--racket` parity fails loudly rather than silently substituting Python.

From the repository root in a prepared review packet:

```bash
python3 generators/94d475bf67ba/workspace/reference_probe.py \
  --per-band 100 \
  --racket \
  --out ../checks/independent-audit.json
```

The probe reads canonical pairs through portable `reviewer_support` helpers, iterates the selected generator, reports observable profiles and named shortcut disagreements, and can compare retained inputs with the real Racket authority. The minimal retained shortcut witness is in `../counterexamples/two_levels_only.json`.
