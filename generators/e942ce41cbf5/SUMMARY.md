# e942ce41cbf5

## Rule

Normalize the blue `1` mask and the red `2` mask to their own origins. The bottom-left control selects the set operation:

- `3`: union
- `4`: intersection
- `6`: symmetric difference (xor)

The bottom-right control selects the red-mask transform:

- `7`: identity
- `8`: rotate clockwise
- `9`: horizontal reflection

Combine the normalized blue mask with the transformed red mask, crop the result to its bounding box, and recolor occupied cells cyan `8`.

## Generator v3.0.0

The selected generator is a semantic curriculum rather than an unconstrained morphology sampler:

- every three consecutive demonstrations expose all three operation controls and all three transform controls;
- seed phase covers all nine operation/transform pairings;
- canvases use the four canonical size profiles;
- both masks are sparse 4-connected polyominoes;
- each sampled pair is rejected unless every operation and every transform produces a distinct **normalized visible output**;
- the public override contract contains only four exact, recoverable axes: `grid_h`, `grid_w`, `op_control`, and `transform_control`;
- `self_check`, `observe_overrides`, `strict_canonical_like`, `rule_mirror`, semantic witnesses, named rivals, and lesson identifiability are executable contracts.

The canonical rule is pinned by `RULE_HASH = "7aa66cd7d9ab"`.

## Review outcome

The original v2.1.0 battery had four blocking stages and only 2/60 exact canonical-profile hits. The v3.0.0 after battery is 12/12 green, including 600/600 strict-canonical semantic draws, 60/60 exact profile draws, 5,310/5,310 accepted override draws, 12/12 identifiable sampled lessons, and 120/120 Python/Racket mirror parity.

Run the focused regressions with:

```bash
PYTHONPATH=shared/runtime:src python3 -m pytest \
  generators/e942ce41cbf5/tests/test_generator_e942ce41cbf5.py -q
```

Run the reusable shortcut census with:

```bash
PYTHONPATH=shared/runtime:src python3 \
  generators/e942ce41cbf5/workspace/shortcut_probe.py --seeds 12 --windows 6
```
