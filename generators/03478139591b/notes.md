# Working notes: 03478139591b

## Current repair decision — 2026-10-26

Generator v1.4.0 (`455ade4456127673f80dcc26936ba2fa6df8c08c766b4cd044b9ecf6aa09e944`) resolves the retained all-zero/Boolean-domain audit: the checker now requires a rectangular 3..15 exact-integer grid containing both 0 and exactly one nonzero color, pins rule hash `e5a2cb4531f0`, and rejects unknown or coercive overrides. Ordinary generation exposes both sides of the complement and is deterministic.

The retained parametric family has two episode-fixed settings. `canonical` is byte-for-byte the selected complement/recolor program. `mark_largest_boundary` first performs that exact step, then finds the largest nonzero 4-connected region created in the intermediate and recolors its boundary with the original foreground color. Four queries include a 30x30 transfer case and do not depend on the requested demonstration/query counts.

Evidence: 15 focused tests; 138 protected-Racket adversarial evaluations against six shortcut families; passed base authoring preflight; source-bound skip-A causal witness replay; 16 public views and 24 first-turn invariance checks. These are reviewer checks only—owner acceptance and training admission were not performed.

## Next useful action

Integrate the returned patch, rerun native owner qualification/acceptance on the live source bytes, then admit only if that fresh replay remains accepted.
