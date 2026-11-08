# Workspace — efb59efe0080

The selected implementation is `../generator.py`; workspace files are retained reviewer tools and are never selected automatically.

- `baseline_generator_2.1.0.py` — byte-for-byte retained selected baseline used for before/after and cyclic comparisons.
- `reference_probe.py` — independent canonical reader, normalized-mask oracle, observed-axis helper, and implementations of the five named plausible rivals. It supports source-bound tests and probes; it is not label authority.
- `lesson_window_probe.py` — materializes consecutive four-pair windows, rotates every member into the query position, and reports any rival that fits the other three demonstrations but changes the query.

Example probe from the packet root:

```bash
cd repo/generators/efb59efe0080/workspace
python3 lesson_window_probe.py \
  --generator ../generator.py --seeds 20 --windows 20 \
  --out ../../../../checks/window-probe/final.json
```

The selected Racket program remains authoritative. Use the probe only after visible-only solve phases are complete because canonical helpers expose answers.
