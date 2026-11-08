# Working notes: e06cc4c752b2

## Current repair decision — 2026-10-26

Generator v1.3.0 (`46a9a3efe8edda531b363e9289a12ee0670080fa8cf3ac3165e6f0b970df6670`) now declares only implemented axes, pins rule hash `4cf331b98beb`, rejects unknown/coercive/contradictory overrides, enforces exact requested marker counts, and rejects requests beyond the separated-layout capacity. Generated singleton markers and their horizontal three-cell expansions remain structurally valid and deterministic.

The retained parametric family has two episode-fixed settings. `canonical` is byte-for-byte the selected isolated-singleton horizontal expansion. `fill_largest_bbox` makes a same-color diagonal staircase become the largest 4-connected component only after expansion, then fills that intermediate component’s bounding box with color 9. The fourth query is 30x30 and contains independent distractor components.

Evidence: 15 focused tests; 138 protected-Racket adversarial evaluations against six shortcut families; passed base authoring preflight; source-bound skip-A causal witness replay; 16 public views and 24 first-turn invariance checks. These are reviewer checks only—owner acceptance and training admission were not performed.

## Next useful action

Integrate the returned patch, rerun native owner qualification/acceptance on the live source bytes, then admit only if that fresh replay remains accepted.
