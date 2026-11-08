# Workspace evidence and tools

The selected implementation is `../generator.py`. This directory contains reproducible review evidence and task-specific probes, not alternate production code.

## Distribution and shortcut probe

`distribution_probe.py` loads any compatible generator file without importing production rival functions and measures:

- generation failures, deterministic replay, uniqueness, shapes, counts, and schedule frequencies;
- visibly causal horizontal and vertical stops, requiring a later non-blocker cell beyond the first blocker;
- adjacent shooters, first-step stops, productive-shooter cardinality, and lowest/highest-shooter stops;
- horizontal-only, vertical-only, cyan, and nonlowest-by-nonlowest crossing witnesses;
- generator `self_check()` findings and every tested three-demonstration lesson window;
- independent rivals for first/last fixed marker caps, cyan restricted to the lowest axes, and blocker semantics restricted to selected marker ranks.

The current schema is `b0e266482663-distribution-probe-v6`.

- Version 2 closed the masked-stop measurement defect by requiring post-blocker background.
- Versions 3–5 added productive-marker, fixed-cap, and secondary-crossing probes while the third review exposed progressively stronger shortcuts.
- Version 6 adds extreme-stop features and an independent blocker-scope renderer so the measurement tool does not rely on the production rival implementations it is auditing.

Example from the repository root:

```bash
python3 generators/b0e266482663/workspace/distribution_probe.py \
  --generator generators/b0e266482663/generator.py \
  --draws 500 --seed-base 20261002 \
  --out generators/b0e266482663/workspace/distribution_after.json
```

`distribution_before.json` is the immutable 3.1.1 baseline measured with the corrected stop definition. `distribution_after.json` is the final 4.6.0 census. `visibility_override_sweep.json` records the final 91,104-case sweep: 60,000 defaults plus all 31,104 declared-axis combinations across the three schedule profiles.

## Red-to-green evidence

Round one and round two evidence remains in this directory and `checks/round2/`. The third adversarial round is under `checks/round3/`:

- `red-multiple-shooters.log` → `green-multiple-shooters-attempt1.log`: exposed lessons compatible with only one productive shooter;
- `red-first-two-shooters.log` → `green-first-two-shooters-attempt1.log`: exposed fixed two-shooter caps;
- `red-secondary-crossing.log` → `green-secondary-crossing-attempt1.log`: exposed cyan restricted to crossings involving the lowest shooters;
- `red-four-shooters.log` → `green-four-shooters-attempt1.log`: exposed first/last-three caps despite a public maximum of four markers;
- `red-distribution-probe-v6.log` → `green-distribution-probe-v6.log`: added an independent blocker-scope audit;
- `blocker-scope-shortcut-v45.json` → `blocker-scope-shortcut-after-v46.json`: exposed and then eliminated marker-specific blocker behavior;
- `focused-tests-v46.log`: final 20-test generator suite;
- `distribution-after-v6.json`: final sampled census;
- `final-stage-summary.json`: all twelve repository stages passing on the final generator hash.

Failed iterations are retained intentionally. They show which assertions distinguished each apparently green intermediate generator from the next stronger semantic contract.
