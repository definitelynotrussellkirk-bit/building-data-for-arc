# Workspace

Reusable review artifacts for generator `056999828b88`:

- `generator_v4_baseline.py` and `test_generator_v4_baseline.py`: immutable assigned-packet comparison copies.
- `run_focused_tests.py`: stages the selected source, canonical row, workspace probes, and focused tests into the portable runtime before running pytest.
- `shape_support_probe.py`: deterministic morphology, profile, witness, declared-rival, four-demo-survivor, and exact-override census.
- `shape_support_before.json`: assigned version-4 600-draw baseline.
- `shape_support_after.json`: final version-6 600-draw report bound to generator SHA-256 `827936454f4766afd7cd45518eb7f7ed7c59d3e0b65c416476e2292ed082c2b8`.
- `shortcut_counterexample.py` / `.json`: regenerate the fixed size-7/8/9 lesson, list each object's geometric features, and compare all eight canonical-fitting shortcut outputs with exact cell-count order.
- `candidate_rival_sweep.py` / `.json`: build 64 canonical-fitting feature/tie-break ordering programs and count survivors over sliding four-demo lessons.

Useful commands from the packet root:

```bash
python3 repo/generators/056999828b88/workspace/run_focused_tests.py
python3 repo/generators/056999828b88/workspace/shape_support_probe.py \
  --generator repo/generators/056999828b88/generator.py \
  --per-band 200 --out /tmp/shape_support.json
python3 repo/generators/056999828b88/workspace/shortcut_counterexample.py
python3 repo/generators/056999828b88/workspace/candidate_rival_sweep.py \
  --generator repo/generators/056999828b88/generator.py \
  --seeds 32 --samples-per-record 12 --out /tmp/candidate_sweep.json
```

The selected implementation remains `../generator.py`; workspace copies and reports are never automatically selected.

October 3 maintainer merge (v6.1.0): retain the existing size-7/8/9 geometry witnesses and compact-output safeguards from review-a484b45ff0084d8c; add disconnected repeated-color objects and color-union/global-frequency rivals from review-70e94a4832b0e4a7 in slot 2. Slot 3 retains the original distinct-color geometry counterexample. The witness tool now reports both generated cases separately. The combined focused portable suite passes 21 tests; the first merge attempt had two tool/coverage failures (19 passed), corrected by keeping the geometry slot independent and updating the probe registry. No full battery or masked-solve rerun on merged bytes, no training admission, Racket unchanged.
