# Working notes: 69dbf44065e2

## Current rule and base-generator decisions

The canonical rule leaves background `0` and walls `5` unchanged, and smears every other input color downward through cells that were background in the original input until the first non-background cell or grid boundary. The selected canonical Racket bytes remain unchanged (`RULE_HASH = b6021aa25bf4`).

The prior generator exposed dead/ambiguous controls and admitted identity or semantically weak scenes. The current generator has four observable exact axes only: `grid_h` (5–30), `grid_w` (5–30), `n_color` (2–8), and `n_walls` (0–4). It rejects bools, malformed values, unknown overrides, and unknown difficulty bands. Its three-profile lesson schedule separately demonstrates wall stopping, colored-seed stopping, and an open long smear; declared rivals cover one-step-only, resume-after-blockers, and treating walls as active seeds.

## Parametric family

`workspace/parametric/` defines one episode-level parameter, `turn = none | left | right`. `none` returns the exact canonical program. The other settings first execute the canonical downward smear (Stage A), then start a horizontal ray from each active seed's input-dependent Stage-A endpoint and extend left or right only through Stage-A background (Stage B). Stage-A trails therefore determine both Stage-B start rows and blockers. Inputs are matched across settings and support 2–6 demonstrations plus 1–4 queries.

## Adversarial finding and repair

A 64-seed probe found one genuine sampler counterexample at seed 53, pair 4 on the 24×7 profile: an extra seed in an interior corridor column created a vertical Stage-A trail that made `right` behaviorally identical to `none`. The repair reserves every column between the two side anchor trails from extra seed/wall placement, and a focused regression pins that exact case. The repaired probe found no survivor among the declared settings or ten plausible bypass rules across 192 episodes, 6,528 rival evaluations, color/count/type/privacy controls, 30×30 stress, thin orientations, and 72 protected-Racket evaluations.

## Current limits

Native authoring preflight, protected causal replay, focused task tests, semantic-gate rotation checks, and public projection/privacy checks pass on the current source. The broad twelve-stage battery was additionally attempted: lint, self-check, and rule smoke passed, then the outer controller timed out before the remaining stages; focused checks cover the changed behavior and the interruption is retained. This is reviewer-ready authoring evidence, not owner source approval, native acceptance, or training admission.
