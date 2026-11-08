# Working notes: 092360ee834f

## Final design

- Canonical rule retained byte-for-byte: count row-0 color-1 cells to get `k`; select the first 4-connected color-3 body component of area `k`; paint it 8 on blank.
- Base generator moved to version 2.1.0 with strict exact-integer overrides, unknown-axis rejection, deterministic local RNG, constructive component placement, a pure-Python rule mirror, and explicit `no_header`, `no_match`, and `multiple_match` probes.
- Native parametric setting is `match_order=first|last`. The alternate reverses the canonical filtered object list and preserves every other reasoning step.
- Supported counts are 2–6 demonstrations and 1–8 queries. Qualification uses the honest minimum of two demonstrations and four queries.

## Adversarial findings and repairs

1. Early minimum lessons let several plausible shortcuts survive on some seeds (`largest_green`, color-blind components, and related area/order rules). Added forced wrong-area green, same-area non-green, and diagonal 4-vs-8 sentinels before matches in one demo and after matches in another.
2. The accepted `target_size=2..8` override domain was not constructible on every fixed profile: target 7/8 failed on 12×14/13×15 layouts, while small targets failed the 30×30 density condition. Added an all-profile/all-target regression, compact edge packing, and deterministic non-green stress density.
3. Relaxing cross-color spacing solved packing but merged the same-area non-green sentinel into color-blind components, allowing `ignore_color_component` to fit some `last` lessons. Reversed that approach: compact the sentinel, shift it one row, keep all visible objects 4-disconnected, and keep green groups 8-disconnected.

## Evidence and limits

- Focused task tests: 17 passed.
- Adversarial tool: 48 episodes, 432 shortcut checks, zero surviving wrong rules; protected Racket both settings.
- Sampler stress: 1,920 cases across 64 seeds, all supported demo counts and query boundaries.
- Authoring preflight: four jobs, 24 parametric labelled pairs, three canonical pairs, 32 protected-Racket evaluations.
- Public projection: 16 one-query views; first-turn check passed 24 invariance mutations and four positive controls.
- Causal witness: wrong intermediate `k+1` changes the final selected object.
- These are bounded authoring/reviewer checks. Owner source review, native qualification/acceptance, and training admission are still required.

## Next action

Owner should inspect the exact source delta, then run unchanged native qualification and fresh acceptance against the returned source binding. Do not treat this reviewer-ready status as acceptance or training admission.
