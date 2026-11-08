# Working notes: ad8f89160989

## Current decision

Reviewer-ready source is generator `3.2.1` plus the native `coverage_mode` family in
`workspace/parametric/`. The default `union` program is byte-for-byte the canonical
rule; `overlap_highlight` keeps count-one halo cells cyan (8) and marks cells covered
by two or more orthogonally adjacent seeds blue (1). The honest minimum lesson is
three demonstrations. Owner source review, native qualification/acceptance, and any
training admission remain separate.

## Base repair

The assigned base was permissive and its advertised controls were not all enforced.
The repaired generator now uses a pure canonical Python mirror, strict unknown/type
checking, constructive distinct-color seed placement, pairwise Manhattan spacing,
and observable interior/edge/corner/mixed profiles. A final self-review found that
`AXES` promised dimensions 5..14 while `self_check` accepted 15..30; the retained
red/green regression tightened this to 5..14 and bumped the source to `3.2.1`.
Canonical Racket authority was not edited.

## Parametric construction

Step A computes an integer coverage grid (0..4) over original background cells.
Step B preserves source seeds, maps count zero to 0 and count one to 8, then maps
counts two through four either to 8 (`union`) or 1 (`overlap_highlight`). Inputs are
setting-neutral and matched. The family supports 3..6 demonstrations and 1..8 stored
queries; qualification uses three demonstrations and four distinct sequentially
revealed queries, including substantive 30x30 scenes.

## Adversarial finding and repair

The first minimum lesson left 86 rival-survivor failures across 96 fresh seeds:
mixed-axis-only and/or different-color-only overlap rules could fit all demos. The
repair constructively includes both a same-color opposite pair and a different-color
perpendicular pair in every minimum lesson, then promotes those shortcuts plus
opposite-only, maximum-only, count-threshold, diagonal, fixed-center, and binary
intermediate rivals into the bounded audit. A separate full-bank failure caused by
placing flexible quadrant motifs before an exact center motif was repaired by
reserving the center anchor first.

## Final evidence

- Focused source-bound tests: `checks/ad8f89160989-tests-final-v3/result.json` (19/19).
- Bounded audit: `workspace/parametric/evidence/adversarial-final.json` (96 seeds,
  192 minimum episodes, 1,344 labeled pairs, 32 boundary episodes, no failures).
- Minimal finding/repair record: `workspace/parametric/evidence/shortcut-finding-and-repair.json`.
- Current inventory: `workspace/parametric/evidence/manifest.json`.
- Protected authoring preflight: `checks/ad8f89160989/qualification/` (40 Racket
  evaluations; owner_accepted=false; training_admitted=false).
- Protected causal replay: `checks/ad8f89160989/causal/`.
- Public boundary: `checks/ad8f89160989/preview-verify.json`, `first-turn.json`, and
  `public-export-check.json` (16 one-query views; 24 invariance mutations; no findings).
- Final source/evidence consistency tool: `checks/ad8f89160989/final_consistency.py`;
  its report records 25 passing hash/status assertions on the exact final bytes.

Finite rival banks and seed sweeps do not prove universal lesson uniqueness or
learning value. The next useful action is owner review of these exact source hashes,
followed by native qualification and fresh acceptance without changing the source.
