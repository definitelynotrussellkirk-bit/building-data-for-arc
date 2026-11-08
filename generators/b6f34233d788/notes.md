# Working notes: b6f34233d788

## Current decision

The reviewed base is repaired and the native family is ready for owner source review. `generator.py` v2.2.0 now rejects unknown/non-exact overrides, samples every declared axis, exposes `observe_overrides`, and uses a semantic `self_check` for 2–6 separated monochrome objects with distinct colors and both zero-hole and positive-hole topology.

The episode-fixed parameter is `ranking={holes_then_area,area_then_holes}`. The default is byte-for-byte canonical. Both settings extract the same object crops and `(holes, area, bbox)` descriptors; only the priority order changes before the unchanged centered horizontal packing. Inputs are setting-neutral and prefix-stable for 2–6 demonstrations and 1–4 queries, with four distinct queries including a substantive 30×30 case.

## Findings repaired during self-review

The first lesson filter was impossible for four-object scenes: 4-row crops centered inside a 5-row output have top offset zero, so the declared `top_aligned` shortcut was exactly canonical. A 3×3 one-hole crop creates a real centering contrast. The protected public-export sweep then found six-object outputs 31–32 columns wide when the 7×4 triple ring was transposed; keeping that crop vertical caps every audited private grid at 30×30. Both failures have regression tests.

The bounded auditor now passes 16 seeds and every legal count combination: 640 requests, 160 distinct inputs, 1,600 public projections, 16 stress checks, 160 cross-setting causal disagreements, zero declared/shortcut survivors and 24 protected-Racket evaluations. The official authoring preflight and protected wrong-order witness also pass. Owner native qualification, exact-source acceptance and training admission remain pending; finite rivals do not prove universal uniqueness.
