# Review workspace for 54099d17f2dd

- `reference_probe.py` is an independent Python transcription of the selected
  rule and a batch Racket parity runner. It deliberately does not import
  production generator helpers for its oracle.
- `analyze_shortcuts.py` verifies every declared canonical shortcut against all
  canonical pairs, searches ordinary scheduled draws for exact counterexamples,
  and records inputs, authority/rival outputs, differing cells, source metadata,
  and optional Racket parity.

From the packet root:

```sh
python3 run_with_racket.py python3 \
  generators/54099d17f2dd/workspace/analyze_shortcuts.py \
  --out ../checks/shortcut-analysis.json
```
