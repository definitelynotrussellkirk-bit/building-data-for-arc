# Workspace

The selected implementation is `../generator.py`.  This directory retains the
source-bound adversarial probe used by the review.

## Realistic modal-color shortcut probe

`modal_shortcut_probe.py` tests a plausible bad rule that keeps the complete
original payload but copies only its modal color.  It scans individual samples
and every consecutive three-example lesson window, recording the first
counterexamples as JSON.

Run from the repository root (no `PYTHONPATH` setup is required):

```bash
python3 generators/6d26bc40cbb2/workspace/modal_shortcut_probe.py \
  --generator generators/6d26bc40cbb2/generator.py \
  --out generators/6d26bc40cbb2/workspace/modal_shortcut_probe_after.json \
  --seeds 300 --max-index 53
```

Retained evidence:

- `modal_shortcut_probe_before_v2.json`: baseline source, where 1,299 of
  15,300 three-example windows failed to refute the realistic shortcut.
- `modal_shortcut_probe_after.json`: final v3.1.0 source, where all 24,300
  multicolor samples refuted it and 0 of 46,800 windows remained ambiguous.

The differing denominators reflect the retained baseline run (100 seeds per
band, indices 0..52) and the larger final run (300 seeds per band, indices
0..53); each report records its exact sampler and source hash.
