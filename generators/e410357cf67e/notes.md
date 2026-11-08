# Current account: e410357cf67e

## Intended rule

A single color-2 border emitter sends a beam inward. Top/bottom edges have precedence at corners. Traversed zero cells become 7; color 4 maps `(dr,dc)` to `(-dc,-dr)`, color 5 maps it to `(dc,dr)`, color 8 stops the beam, and leaving the grid stops it. The canonical Racket authority is unchanged and pinned by normalized hash `ca02c94ead8c`.

## Current generator

Version `4.0.0` uses exact axes `grid_h`, `grid_w`, and `profile`. Five profiles cycle by sample index: corner/two-mirror/wall, two-mirror/boundary, corner/one-mirror/wall, one-mirror/boundary, and straight/wall with off-route mirror decoys. Four demonstrations are required; every five-pair query rotation refutes the declared rivals.

Canonical-size/palette anchors occur every other schedule block; intervening blocks vary dimensions by difficulty. Keyed randomness varies source side, reflection coordinates, walls, and decoys. Unknown, mistyped, and out-of-range overrides fail loudly.

## Reversed decisions

- The old validator treated corner emitters as ambiguous. This was reversed because the authority explicitly gives top/bottom precedence and canonical pair 2 uses a corner.
- The old validator required a mirror hit. This was reversed because canonical pairs 2 and 3 are lawful straight paths.
- The old generator advertised generic palette/texture/count axes. They were removed because they were dead, singleton, ignored, or not observable.
- The old random-scatter curriculum was replaced because it did not guarantee active-wall, corner, straight, or rotation-safe rival evidence.

## Evidence and known limits

Final selected generator SHA-256: `b84e46e019265b259448dd0004d140a77ce7734166223b403e62dea818392a10`.

- 62 focused tests pass.
- Full after battery: 12/12 green.
- Strict semantic gate: 600/600; canonical acceptance 4/4.
- Override matrix: 17,460/17,460 accepted with zero findings.
- Lesson census: 300/300 materialized, 0/300 production ambiguity, 0/1,500 rotated ambiguity, 1,022 unique inputs.

These are finite checks against seven declared rivals, not a proof of unique induction. The grammar intentionally stays sparse and bounded; arbitrary mirror loops and dense obstacle fields are outside the generated domain. Catalog training safety remains unverified.

Retained evidence: `counterexamples/review-9a3cfcbadd2ba12e-v0001/`. Reviewer tool: `workspace/reference_probe.py`.
## Current reviewer considerations

Source SHA-256: `b84e46e019265b259448dd0004d140a77ce7734166223b403e62dea818392a10`.

# Decisions for e410357cf67e

## D1 — leave the Racket authority unchanged

**Prior choice:** the baseline generator already described the correct color roles and the authoritative rule smoke passed. The historical reason for the exact Racket implementation is not recorded here.

**Decision:** do not edit the Racket source; pin `RULE_HASH = "ca02c94ead8c"` and repair the generator around it.

**Alternatives considered:** changing corner semantics, requiring every mirror to be hit, or treating a wall as mandatory. All would contradict labeled canonical inputs. The rule matched 4/4 labels and the final Python mirror, so a source change would create unnecessary authority risk.

## D2 — replace ten mostly fictional axes with three observable axes

**Prior choice:** the baseline advertised `palette_kind`, `n_mirrors`, `n_walls`, singleton palette/count fields, density, position bias, and texture aliases. The original rationale appears to have been generic generator-template coverage, but no task-specific evidence was recorded and several values were never consumed.

**Decision:** retain only `grid_h`, `grid_w`, and `profile`. Each is consumed through keyed draw provenance, validates exact types/ranges, rejects unknown keys, and can be recovered from the returned grid.

**Rejected alternative:** retain legacy aliases for compatibility. That would preserve misleading controls and enlarge the override matrix without improving training data.

## D3 — use a five-profile cyclic teaching schedule

**Decision:** make the period equal to five and require four demonstrations. The profiles jointly teach corner precedence, each mirror handedness, wall stopping, boundary stopping, and off-route irrelevance.

**Why five:** two separate corner profiles are required so horizontal-corner precedence remains refuted after either one is held out. Three active-wall profiles keep `ignore_walls` refuted under every rotation. Two two-mirror profiles preserve handedness evidence when one is the query.

**Rejected alternatives:**

- Pure random scatter: cannot guarantee branch or rival coverage in a lesson.
- Four profiles: one held-out query could remove the only witness for a branch.
- More than five: unnecessary for the declared rivals and increases lesson cost.

## D4 — allow border mirrors in corner profiles

A beam starting at a corner under top/bottom precedence remains on the side border until something redirects it. Therefore a corner example that also teaches reflection needs a lawful mirror on that border. The authority permits this, and the current validator treats border mirrors as lawful.

**Risk:** canonical examples place hit mirrors in the interior or use a straight corner path, so border mirrors extend beyond the observed placement pattern. The extension is minimal, semantically direct, and independently checked by Racket. The straight corner profile remains represented by canonical support and the schedule's corner behavior is not inferred only from this extension.

## D5 — accept zero-hit and off-route mirrors

**Prior choice:** the old validator required at least one mirror hit, apparently to force a nontrivial bounce.

**Decision:** require at least one mirror somewhere but not on the beam. Canonical pair 3 has a straight path with off-route mirrors, and canonical pair 2 is a straight corner path. The beam must still paint at least two cells and terminate lawfully.

**Rejected alternative:** special-case the two canonical grids. That would pass fixtures without correctly owning the rule domain.

## D6 — combine canonical anchors with broader dimensional variation

Every other five-sample block uses profile-linked dimensions/palettes that match canonical profiles. Intervening blocks use difficulty-aware dimensions across the declared valid ranges. This produced 34/60 exact and 40/60 envelope matches in the profile-floor gate while preserving larger easy/medium/hard variety.

**Rejected alternatives:** always use canonical dimensions (too template-like) or sample all dimensions uniformly (could miss the profile floor and dilute source-shaped examples).

## D7 — make the canonical shortcut explicit

`ignore_walls` fits all four canonical labels, so it is listed in `CANONICAL_SHORTCUTS` rather than treated as an accidental test. Active-wall profiles place at least one empty cell beyond the wall, guaranteeing different canonical and ignore-wall outputs.

The retained old-source lesson in `checks/original-ignore-walls-ambiguous-lesson.json` demonstrates why this matters: four baseline demonstrations fit the shortcut and the held-out query does not.

## D8 — use a strict, independent analyzer and Python mirror

The analyzer traces directional state, records hit/off-route mirrors and termination, and detects loops/fuel exhaustion. The Python mirror is separate from construction rather than returning a precomputed path. This lets tests compare generated structure, canonical labels, rivals, and Racket execution through independent routes.

**Failure modes considered:** source duplication, answer-color leakage, bool-as-int acceptance, ragged grids, corner ambiguity, mirror loops, and wall pass-through. Focused tests cover each relevant case.

## D9 — retain exact counterexamples and a probe tool

The selected counterexample packet preserves the two canonical inputs rejected by the old validator, an active-wall shortcut breaker, and the old-source ambiguous lesson. `workspace/reference_probe.py` gives future reviewers a cheap way to inspect exact axes and all rotations without reconstructing ad hoc scripts.

## D10 — stopping decision

Stop after the final generator hash passed 62 focused tests, the 12-stage battery, the 17,460-draw override matrix, the 300-lesson/1,500-rotation census, retained counterexample replay, and a post-repair visible solve. Further expansion into arbitrary multi-bounce mazes would increase loop risk and grammar complexity without evidence that it is needed for this review.
