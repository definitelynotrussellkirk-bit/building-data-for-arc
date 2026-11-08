# Working notes: cf787ae40567

## Provenance

The assigned baseline was version 1.3.0 at SHA-256 `79c02ed38e8cfce63bf3fc0f76ff7786b08a121cf307b2e337ea60920d2f94c7`. `evidence/associated_notes.jsonl` was empty, so no prior return was used as a repair lead and the original rationale for its pseudo-axes/textures is unknown.

The selected canonical Racket authority was retained byte-for-byte. Its normalized hash is `5d3366b26415`.

## Baseline findings

- The three canonical pairs contain only separated interior color-2 seeds. Therefore both `5 * seed_count` and “sum every clipped plus size without deduplicating overlap” fit all canonical labels.
- The baseline ordinary sampler usually generated broad random scenes without an executable lesson contract. The strict profile census found `0/60` exact canonical-profile hits and only `2/60` envelope hits; medium and hard had zero support.
- `RULE_HASH` was absent. Two advertised axes were not probeable, `position_bias` was effectively fixed, four helpful textures were dead, negative textures overlapped the advertised valid domain, and `self_check` accepted minimal impostors.
- The semantic gate reported `NO_CONTRACT`, so a syntactically valid generated lesson could reinforce either canonical-fitting shortcut.

## Selected design

Version 2.0.0 replaces the misleading generic knobs with one observable `profile` axis:

1. `canonical` preserves the exact canonical size/palette/object-count family.
2. `overlap` creates exactly one pair of intersecting plus masks and distinct seed colors.
3. `edge` creates clipped, mutually disjoint masks with a shared seed color.
4. `mixed` combines at least one boundary seed and exactly one overlapping pair with distinct colors.

Every consecutive four sample indices contain all four profiles. The seed-root phase is `(seed ^ (seed >> 1)) & 3`; this preserves the four-window guarantee while preventing the pinned profile-floor seed recipe from aliasing to one profile. Each profile owns disjoint target widths, and together they exhaust `5..28`, the truthful finite output alphabet of this teaching distribution.

The generator now fails closed on unknown overrides and unsupported difficulty names, validates a strict four-profile grammar, observes the profile from the returned grid, pins the rule hash, and publishes executable rivals/witnesses plus `lesson_identifiable`.

## Tests and tools

`tests/test_generator.py` contains 58 task-local tests. They cover canonical parity through an independent oracle, all profile overrides and schedules, grammar mutations, complete codomain support, pinned per-band profile support, canonical-fitting rivals, cyclic lesson identifiability, and the reusable lesson probe.

`workspace/reference_probe.py` independently computes plus masks, unions, edge/overlap signatures, and the two canonical-fitting rival outputs. It deliberately does not import production geometry helpers.

`workspace/lesson_probe.py` is a source-hashed CLI that assembles cyclic four-demo/one-query windows from the live sampler, reads the live `LESSON_COMPETITORS` registry, compares outputs with the independent oracle, and emits compact JSON. It is authoring evidence, not Racket authority.

## Measured final state

- Full after battery: 12/12 stages green on generator SHA `a9c8dfbccf9b4603946e6f91d7a8722eb771f064a7d21cdcdb43ad39f16e05da`.
- Task-local portable tests: 58 passed.
- Strict profile floor: 21/60 exact canonical-profile hits (`easy 7/20`, `medium 6/20`, `hard 8/20`).
- Production lesson census: 300/300 lessons materialized and identifiable, 0 ambiguous, 0 scoring errors, 1,449 unique inputs among 1,500 pair positions; both named rivals refuted in 100/100 lessons per band.
- Independent cyclic probe: 768/768 lessons passed over seeds `0..63`, starts `0..3`, and all three bands; 1,475 unique inputs, all widths `5..28`, both rivals refuted in every lesson.

## Limitations and future checks

The sampler is intentionally a bounded curriculum, not the full lawful rule domain: canvases are 5–14 cells per side, at most six seeds are used, and output widths are 5–28. The finite rival registry does not prove universal identifiability. Any change to profile construction, width allocation, or schedule phase should rerun the strict battery, 100-lessons-per-band census, portable task tests, and `workspace/lesson_probe.py`.
## Current reviewer considerations

Source SHA-256: `a9c8dfbccf9b4603946e6f91d7a8722eb771f064a7d21cdcdb43ad39f16e05da`.

# Decisions: cf787ae40567

## D1 — Preserve the selected Racket authority

**Choice.** Do not change the canonical program; pin `RULE_HASH = "5d3366b26415"` and treat Racket as label authority.

**Rationale.** Canonical outputs and generated-rule smoke tests already agreed. The defect was in what inputs/lessons were sampled and validated, not in the transformation.

**Alternatives rejected.** Rewriting the rule in Python or editing the canonical row would increase authority risk without fixing the curriculum ambiguity.

**Failure mode / limit.** The Python `rule_mirror` could drift; independent-oracle tests plus Racket rule-smoke/authority-sync cover this risk.

## D2 — Replace pseudo-axes with one observable semantic profile

**Choice.** Remove unprobeable palette/count declarations, fixed `position_bias`, dead helpful textures, and negative textures from the public control surface. Advertise only `profile ∈ {canonical, overlap, edge, mixed}`.

**Original rationale.** Unknown. The baseline retained no associated notes explaining the pseudo-axes or textures.

**Rationale.** A control should be visible in returned data and exactly honored. The four profiles directly represent the two operations hidden by canonical examples.

**Alternatives rejected.** Keeping many cosmetic axes would preserve matrix noise and silently ignored overrides. Marking all old controls diagnostic would still expose misleading API surface.

**Probe.** Override tests verify every profile is observable and rule-correct; unknown keys and invalid values fail closed.

## D3 — Keep a canonical anchor profile in every band

**Choice.** Reserve one profile for 7×7, 8×8, or 9×9 square inputs, one to three separated interior color-2 seeds, and widths 5/10/15.

**Rationale.** The baseline had 0/60 exact canonical-profile hits. Anchors preserve source-task identity while the other profiles teach the missing semantics.

**Alternative rejected.** A fully broad generator had more superficial variety but weak task-source support.

**Measured result.** Strict profile floor is 21/60 exact with all bands represented.

## D4 — Use explicit edge and overlap counterfactuals

**Choice.** `edge` contains clipped, mutually disjoint masks; `overlap` contains exactly one intersecting pair; `mixed` contains both.

**Rationale.** These are minimal counterexamples to the two canonical-fitting shortcuts. Separating them makes each causal operation legible, while mixed examples test composition.

**Alternatives rejected.** Relying on random placement made witnesses probabilistic and allowed complete lessons without them. Dense/random seed fields also made the intended operation harder to infer and harder to validate exactly.

**Failure modes.** Overlap construction can accidentally create multiple intersections; edge construction can accidentally overlap. Structural profile recognition and target-width assertions reject either case.

## D5 — Guarantee all four profiles in every four-demo window

**Choice.** Set `EXAMPLES_NEEDED = 4` and schedule profile by sample index plus a seed-root phase.

**Rationale.** Witness frequency alone is insufficient: the actual demonstration window must contain the evidence. A four-cycle gives a deterministic complete lesson.

**Rejected first attempt.** Index-only phase passed local windows but starved a pinned hard-band profile census. A linear seed phase then aliased with another deterministic seed/index recipe. The final phase `(seed ^ (seed >> 1)) & 3` breaks that alias while preserving every length-four window.

**Probe.** Tests cover consecutive windows, multiple seed roots, the exact pinned profile-floor recipe, 300 production lessons, and 768 cyclic lessons.

## D6 — Declare and exhaust the finite teaching codomain

**Choice.** Use all one-row width states 5 through 28 exactly as the ordinary sampler's output alphabet, partitioned across the four profiles.

**Rationale.** The first repair truthfully generated only a small finite set but did not declare/exhaust it, producing low-output-diversity lint. Explicit construction makes the support auditable and reproducible.

**Alternatives rejected.** Claiming unbounded diversity would be false. Extending to width 29/30 was not necessary to distinguish the target shortcuts and would complicate the mixed constructions.

**Limit.** This is a curriculum codomain, not the full Racket rule domain.

## D7 — Validate exact lawful grammar, not generic grid shape

**Choice.** `self_check` rejects malformed grids, no-seed/too-many-seed scenes, reserved input color 8, union widths over 30, and any scene not recognized as one of the four profiles.

**Rationale.** The baseline checker accepted all-background, short-line, solid-block, and negative-texture impostors. Structural validation prevents mislabeled or shortcut-friendly data from being silently admitted.

**Alternatives rejected.** A permissive checker plus a separate negative-texture list left contradictory definitions of “valid.” This task has no advertised degenerate textures now.

## D8 — Make shortcut claims executable

**Choice.** Declare `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, and `lesson_identifiable` as executable functions/contracts.

**Rationale.** Narrative intent cannot be gated. The two rivals were first verified to fit every usable canonical pair, then required to fail on generated demonstrations.

**Limit.** The registry is finite and must be extended when new plausible hypotheses are discovered.

## D9 — Add an independent oracle and reusable lesson tool

**Choice.** Keep plus geometry in `workspace/reference_probe.py` independent of production helpers; add `workspace/lesson_probe.py` for source-hashed cyclic lesson audits.

**Rationale.** Tests that call only the production mirror can preserve a shared bug. The reusable CLI lets future reviewers rerun broad lesson checks without rebuilding an ad hoc script.

**Probe.** The tool itself is covered by task tests and its 64-seed/4-start run passed 768 lessons.

## D10 — Keep measured limits explicit

**Choice.** Report the bounded canvas, seed-count, width, and rival-registry limits rather than claiming universal task induction or training admission.

**Rationale.** A generator review establishes a controlled curriculum and source-bound evidence, not a theorem about every model or every lawful grid.
