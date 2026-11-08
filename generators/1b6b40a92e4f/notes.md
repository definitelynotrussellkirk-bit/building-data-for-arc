# Working notes: 1b6b40a92e4f

## Current decision

The reviewed base is repaired and the native family is ready for owner source review. `generator.py` v2.1.0 now rejects unknown/non-exact overrides, samples every declared axis, exposes `observe_overrides`, and uses a semantic `self_check` that requires one separated 4-connected component of each source color and a meaningful normalized overlap/exclusive-cell relation.

The episode-fixed parameter is `green_pose={as_is,rotate_cw}`. The default is byte-for-byte canonical. The alternate normalizes the input-derived green footprint, rotates that intermediate clockwise, and performs the unchanged red/green overlay. Inputs are setting-neutral and prefix-stable for 2–6 demonstrations and 1–4 queries; every query bank has four distinct inputs including one substantive 30×30 boundary case.

## Adversarial review and evidence

The bounded auditor sweeps 16 seeds, all 2–6 demonstration counts, all 1–4 query counts and both settings: 640 requests, 160 distinct inputs, 1,600 public projections, 16 stress checks, 160 cross-setting causal disagreements and zero declared/shortcut survivors. It also replayed 24 selected labels through protected Racket. The official authoring preflight replayed both settings at seeds 0 and 17 and retained the original canonical labels. A protected wrong-intermediate witness replaces the rotated green coordinates with the unrotated coordinates and changes the final grid.

Owner native qualification, exact-source acceptance and any training admission remain pending. The finite rival bank is not a proof against arbitrary programs.
