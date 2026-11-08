# Working notes: 63784d19dd2d

## Current native parametric proposal — reviewer return 2026-10-25

Decision: retain production `generator.py`, rule hash `7e42f2b65a1e`, and the selected canonical Racket source unchanged. The task-local native family adds the episode-fixed parameter `overlap_mode={transform_only,mark_b_overlap}`. `transform_only` is byte-identical to the selected canonical program. `mark_b_overlap` infers the unique transform mapping panel A to B, applies it to panel C, then recolors only occupied transformed-C cells whose output coordinates are occupied in B.

The alternate rule has a real sequential dependency. Step A infers the A→B transform; the intermediate is transformed C and its coordinate support; step B applies the B-overlap mask to that transformed support. A protected-Racket counterfactual that substitutes untransformed C changes 22 cells on a qualified 9×29 query.

The deterministic matched-input sampler supports 2–6 demonstrations and 1–4 prefix-stable sequential queries. The largest lawful unchanged-grammar input is 9×29 because the input width is `3N+2`; `N=10` would exceed ARC's 30-column limit. The first two demonstrations distinguish both settings from eight declared finite rivals.

Current evidence:
- `workspace/parametric/evidence/manifest.json`: exact source inventory.
- `checks/63784d19dd2d/qualification/{qualification,execution}.json`: native qualification for both settings, seeds 0/17, three demonstrations and four queries; 40 protected-Racket evaluations.
- `checks/63784d19dd2d/self-audit.json`: 36 episodes, 222 labeled pairs, 108 protected-Racket evaluations, no declared-rival survivor.
- `checks/63784d19dd2d/stress-32-seeds.json`: 384 episodes and 2,368 labeled pairs over 32 seeds.
- `checks/63784d19dd2d/causal/{witness,replay-final}.json`: source-bound wrong-intermediate replay.
- `checks/63784d19dd2d-final-tests/result.json`: 35 staged tests passed.

Status is reviewer-ready, not owner-accepted. Next action: integrate these exact bytes, rerun native qualification and protected witness replay on the live tree, then make the separate owner acceptance and training-admission decisions.
