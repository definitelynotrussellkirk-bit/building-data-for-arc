# Current notes: b19deac47327

## Intended rule

Exactly one opposite border pair is solid in two distinct colors. Each color-1 marker projects the matching border color into the adjacent background cell toward that border. Horizontal borders use top/bottom halves; vertical borders use left/right halves. On an odd projection axis, the exact middle index belongs to the first/top-left side because the authority tests `2 * axis < extent`.

Canonical pin: `RULE_HASH = 2b2e46dd36cc`. The canonical Racket authority was not changed in this review.

## Selected generator

Version `2.1.0`; SHA-256 `14284b3bd817e139cf615486973e192da5ec84a97f50c200832e23cd682551ed`.

The approved v2.0 design remains intact: eight exact observable controls, a four-slot semantic schedule, independent parsing/mirroring, executable witnesses/rivals, and retained canonical-shortcut counterexamples. Approved return `review-a8e2e34d9efd7169:v0001` was used only as a lead; current claims come from this packet’s fresh checks.

## Current repair decisions

1. Public `seed` and `sample_index` require exact integers; bools, floats, and strings are rejected. Sample indices must be nonnegative. Difficulty is validated before schedule arithmetic or generation.
2. Default heights now exercise the strict canonical envelope without weakening lesson anchors. `cross_horizontal` and `cross_vertical` remain at height 12; `tie_vertical` samples 12–16; `tie_horizontal` samples odd heights 13/15 so its midline witness remains valid.
3. An earlier attempt to vary every profile was reversed after it broke three lesson-identifiability tests. The failed evidence is retained at `checks/tdd-green-canonical/`.
4. `counterexamples/canonical_shortcuts.json` is rebound to v2.1.0/final hash; its semantic witnesses are unchanged.

## Parametric proposal

`workspace/parametric/prototype.py` is a separate, unapproved extension with episode-level `projection_depth ∈ {1,2}`. Depth 1 is the exact canonical default; depth 2 paints two cells toward the matching border. Protected Racket labels, independent Python mirrors, public/private episode separation, canonical replay, and alternate-parameter scoring are retained in `checks/parametric/projection-depth-v1/`. This prototype does not modify selected execution or grant variant/training approval.

## Final evidence

- Final enumerated battery: 12/12 green (`checks/after-enumerated/`).
- Portable task tests: 25/25 green (`checks/task-tests/`).
- Strict semantic sample: 600/600.
- Profile floor: exact 31/60 overall and at least 9/20 in each band; envelope 60/60.
- Override matrix: 849 cases, 76,410/76,410 accepted, zero findings/warnings.
- Lesson census: 300/300 materialized, 1,200 unique inputs, zero production or query-rotation ambiguities against declared rivals.
- Post-repair visible solve: first attempt, 3/3 demonstrations; prior exposure declared yes, reference consultation during solve no.

## Known limits

Evidence is finite and only refutes declared deterministic rivals. The four-profile defaults intentionally prioritize complete-lesson identifiability over independent uniform sampling. Exact overrides expose the legal cross-product, but no claim is made that every conceivable hypothesis is ruled out or that this review grants training admission.
