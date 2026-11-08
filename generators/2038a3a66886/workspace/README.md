# Workspace tools

`reference_probe.py` is an independent, reproducible semantic audit for this
sampler. It checks all five canonical pairs with a separate authority
implementation, confirms that both canonical-fitting shortcut rules really do
survive the canonical demonstrations, measures every declared row pattern in
each difficulty band, records exact canonical-profile hits, and verifies that
every consecutive three-example schedule window refutes both shortcuts.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/2038a3a66886/workspace/reference_probe.py \
  --per-band 100 --lesson-starts 25 \
  --json-out ../checks/reference-probe.json
```

The tool exits nonzero on oracle mismatch, nondeterminism, identity lessons,
missing patterns, missing profile anchors, missing rival counterexamples, or an
unidentifiable three-demo window.
