# Working notes: 01f4294de005

## 2026-10-26 reviewer build

### Canonical generator repair

The prior ordinary sampler reserved row 1 globally, so it never exercised lawful
body contact with the legend boundary.  The final `1.4.0` generator places the
body in all rows below the legend and exposes `top_contact=0|1` as an honest,
observable axis.  It also:

- validates `seed`, `sample_index`, and every override as exact nonnegative
  integers where applicable (Booleans are rejected);
- rejects unknown overrides instead of silently ignoring them;
- removes the redundant/dead `texture` axis and keeps the exact `decoy` axis;
- uses keyed draw provenance for every declared axis;
- retries whole-scene placement, largest components first, so feasible small
  canvases do not fail because a greedy early placement stranded the last blob;
- verifies the generated observables before returning, so requested object
  counts are never silently reduced.

A focused regression retains the exact former small-canvas failure
(`grid_h=6`, five blobs, no top contact), and ordinary generation now includes
both row-1 contact and blank-row cases.  The final bounded sweep observed 126
contact and 162 blank cases across 288 ordinary draws.

### Native parametric family

The family parameter is `echo_mode`:

- `none` is the byte-exact canonical Racket rule: measure each orange component
  by area and recolor it with the corresponding left-to-right legend color.
- `matching_marker` performs that same area-to-color lookup, then consumes the
  selected color to locate its unique singleton marker and echoes the normalized
  source shape at that marker.

Inputs are matched across settings.  Each scene contains orange components of
every area `1..N`, a unique singleton marker for every legend color, randomized
source/marker order, varied connected shapes, boundary contacts, and distractors.
The adapter supports 2–6 demonstrations and 1–4 query prefixes while storing four
distinct queries; the query profiles are 9x12, 16x20, 23x27, and a substantive
boundary-spanning 30x30 scene.  Prefix generation is stable, so revealing one
query at a time does not expose a future-input count or alter the first turn.

### Adversarial findings and repairs

The initial build was not treated as sufficient.  Attacks found and repaired:

- a disconnected six-cell shape in the sampler;
- a bounding-box-area proxy that could fit the minimum lesson;
- inadequate source-position crossing at fixed area;
- Boolean grid cells comparing equal to integer zero in Python;
- loose scalar request handling in the canonical generator;
- a dead/redundant texture declaration and conflicting override semantics;
- noncanonical draw-label provenance for the decoy axis;
- greedy placement failure on a feasible minimum canvas.

The retained `adversarial_probe.py` attacks ten relevant bypasses: no echo,
source left-to-right/top-to-bottom rank, nearest marker, width, height,
bounding-box area, reversed palette, first marker, and marker-position rank.
On final bytes it checked 128 seeds, 256 two-demonstration episodes, 1,536
labelled pairs, six size profiles, crossed source/marker positions, strict
malformed requests, and 18 protected-Racket jobs / 204 evaluations.  No tested
rival fit every demonstration while changing a query answer.

### Final authoring evidence

- Focused pytest and packet task-tests: 34/34 passed.
- Native `defect_lint`: passed.
- Native `override`: passed with no findings or warnings; unknown keys rejected.
- Source inventory: final manifest binds 11 files.
- Authoring preflight: 2 settings, 4 jobs, 24 parametric labelled pairs,
  3 canonical base pairs, and 32 protected-Racket evaluations.
- Causal witness: protected-Racket `wrong_intermediate` replay changes 10 final
  output cells and rechecks against the final qualification source binding.
- Public projection: 4 episodes / 16 single-query views; 24 first-turn invariance
  checks and 4 positive controls passed.
- Negative export attack: injecting a query answer into a public view was rejected
  because its exact visible bytes/hash changed.

### Status and finite limits

The artifact is reviewer-ready only.  Owner-side native qualification, witness
replay, exact-source acceptance, and any later training admission remain pending.
The finite rival set and finite seeds do not prove universal uniqueness, and the
causal interpretation is reviewer-authored even though both programs and changed
outputs were protected-Racket replayed.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/01f4294de005/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
