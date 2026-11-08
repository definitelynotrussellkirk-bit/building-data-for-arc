# Working notes: be7f70e60fb7

## Review diagnosis — 2026-09-28

The imported `2.0.1` generator was a generic template rather than a faithful task curriculum:

- It omitted the required `RULE_HASH` pin.
- It advertised many axes that were inert, only partially honored, or mutually inconsistent. The before override gate reported 10,168 findings across 41,760 draws and accepted unknown keys.
- Negative fixtures (`no_pair`, `diagonal_only`, `adjacent_pair`) were mixed into the ordinary texture domain, while several “helpful” texture values were byte-identical no-ops.
- Every ordinary example added a singleton even though none of the five canonical inputs contains one.
- Easy and hard had zero canonical-profile support; pooled exact support was only 3/60 and envelope support 8/60.
- No semantic contract, witnesses, rivals, or lesson-level identifiability check existed.

## Selected design

The Racket authority was left unchanged and pinned as `RULE_HASH = "d264380c5850"`. The public surface was reduced to one exact, input-observable axis: `scene_profile`.

A deterministic four-profile schedule now teaches the complete rule:

- `canonical_two_pairs`: two positive branches, one horizontal and one vertical.
- `canonical_three_pairs`: multiple simultaneous transformations, preventing “change only one color” shortcuts.
- `alignment_decoy`: a separated 45-degree pair stays unchanged, falsifying “connect every repeated color.”
- `cardinality_decoys`: a singleton and an aligned triple stay unchanged, falsifying “connect any aligned nonzero color” and “erase noise.”

All profiles preserve exact canonical shape/palette signatures. Layout randomness is keyed by seed, sample index, profile, and difficulty band. Public overrides are rejected unless declared and are recovered exactly by `observe_overrides`.

## Deliberate exclusions

- Connectable segments never cross or pass through another pair’s endpoint. The canonical examples do not identify overwrite precedence for crossings; admitting them would teach an implementation accident of color iteration rather than the demonstrated concept.
- Diagonal near-misses are restricted to separated 45-degree pairs. This gives a visible, unambiguous alignment contrast while keeping the observer exact.
- Difficulty bands alter deterministic layouts but not the semantic curriculum. The task has no canonical evidence for a distinct easy/medium/hard rule distribution.

## Semantic contract

The generator declares witnesses and executable rivals for:

- bounded segment versus whole-axis fill;
- all valid pairs versus lowest-color-only;
- aligned versus diagonal repeated colors;
- exactly-two versus aligned triples;
- preservation versus singleton deletion.

`lesson_identifiable` requires all four profiles and rejects a lesson if any named rival survives.

## Reproducible review probe

`workspace/audit_curriculum.py` audits a seed prefix across all three bands. It checks schedule coverage, determinism, override observability, self-checks, non-identity transformation, lesson identifiability, and rival refutation. The retained 100-seed run covered 1,200 generated cases with zero failures and all five rivals refuted.

## Verification result

The after battery passed all 12 stages. Canonical-profile support improved to 60/60 exact and 60/60 envelope, with 20/20 exact hits in each difficulty band. Task tests pass, the Racket authority remains synchronized, and the generator source is input-pure and deterministic.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `fa1dca85ff17f5db44f13b6103fa2c4de1ef52bba0cc5b8fdbbae62a16150196`.

# Decisions for `be7f70e60fb7`

## D1 — Keep the canonical Racket authority unchanged

**Choice.** Preserve the selected Racket rule and pin `RULE_HASH = "d264380c5850"`.

**Original rationale.** Unknown; the imported Python generator omitted the pin. The before rule smoke, Racket lint, authority sync, and direct canonical replay all showed that the authority correctly solves the five canonical pairs.

**Alternatives considered.** Change iteration order, special-case crossings, or narrow the rule to generated layouts.

**Probe.** The Python mirror was replayed on every canonical pair and compared with the retained authority. The after `rule_smoke`, `racket_lint`, and `authority_sync` stages pass.

**Failure mode avoided.** Changing a correct authority to compensate for a poor generator would silently redefine the task.

**Limitation.** The rule’s overwrite behavior on crossing segments remains implementation-defined because the canonical data contains no crossing example.

## D2 — Match exact canonical shape/palette support

**Choice.** Generate only the five observed `(height, width, palette-size)` signatures: `(8,8,3)`, `(8,10,3)`, `(9,8,4)`, `(9,9,4)`, and `(10,10,4)`.

**Original rationale.** The imported size bands were generic (`5..12` by `7..14`) and appear to have come from a reusable template rather than this task.

**Alternatives considered.** Keep broad size ranges; use only literal canonical dimensions; sample the rectangular envelope without exact signatures.

**Probe.** The before profile floor found only 3/60 exact hits and zero support in easy and hard. The after profile floor finds 60/60 exact hits, 20/20 in each band, while retaining multiple layouts per signature.

**Failure mode avoided.** Training mostly on off-profile dimensions can make a small model learn distribution cues that do not transfer to the canonical task.

**Limitation.** This is intentionally conservative: it does not claim the rule fails on other sizes, only that the training distribution should remain grounded in demonstrated support.

## D3 — Replace nine pseudo-axes with one semantic profile axis

**Choice.** Expose only `scene_profile`, reject all unknown keys, and recover the selected profile from the returned grid.

**Original rationale.** Unknown. The imported axes included singleton domains, aliases, inert controls, invalid size requests, and textures that were either no-ops or negative fixtures.

**Alternatives considered.** Repair every imported axis; keep decorative palette/texture controls; expose raw counts, orientations, and dimensions separately.

**Probe.** The before override stage reported 10,168 findings across 41,760 draws and accepted unknown keys. The after override stage is green with no findings or warnings and rejects unknown keys.

**Failure mode avoided.** Metadata says one thing while the actual grid says another, corrupting conditional training and evaluation.

**Limitation.** Fine-grained controls can be added later, but each must be constructive, composable, and observable before becoming public.

## D4 — Use a four-profile deterministic semantic curriculum

**Choice.** Cycle `canonical_two_pairs`, `canonical_three_pairs`, `alignment_decoy`, and `cardinality_decoys` in every four-example window.

**Original rationale.** The imported generator randomized one to three pairs and systematically included a singleton, but had no schedule or lesson contract.

**Alternatives considered.** Independent random sampling; only canonical-positive scenes; a larger schedule with one profile per individual predicate.

**Probe.** Unit tests verify every four consecutive examples cover all profiles in all bands. The semantic gate materialized 12 lessons and judged all 12 identifiable. The 100-seed curriculum audit repeated this over 1,200 cases.

**Failure mode avoided.** A short lesson can otherwise omit a critical precondition and leave a simpler rival fully consistent with the demonstrations.

**Limitation.** Four demonstrations are required rather than the imported three. This is the minimum schedule that deterministically carries all selected contrasts.

## D5 — Put both positive orientations in ordinary scenes

**Choice.** Every `canonical_two_pairs` scene has one horizontal and one vertical pair; three-pair scenes contain both orientations.

**Original rationale.** The original generator flipped orientation independently and could produce a short lesson with only one branch.

**Alternatives considered.** Random orientation balance; separate horizontal and vertical profiles.

**Probe.** `analyze_grid`, witnesses, unit tests, and curriculum audit assert both branches are present and active.

**Failure mode avoided.** A row-only or column-only solver can fit an underpowered lesson.

**Limitation.** The enforced within-scene balance is stronger than the canonical data requires, but it changes only nuisance layout, not the rule.

## D6 — Add alignment and cardinality near-misses

**Choice.** Add one separated diagonal repeated color in `alignment_decoy`, and one singleton plus one gapped aligned triple in `cardinality_decoys`. These cells are preserved.

**Original rationale.** The imported generator’s negative textures were mixed into the valid domain and often failed self-check; ordinary scenes only exercised aligned pairs plus a singleton.

**Alternatives considered.** No negative controls; adjacent pairs; no-pair scenes; arbitrary diagonal offsets; four-or-more occurrences.

**Probe.** Named rivals connect diagonal pairs, connect aligned colors with count `>=2`, or erase singletons. Each rival is falsified in every scheduled lesson; witness/rival claims pass 60/60 sampled checks.

**Failure mode avoided.** “Connect every repeated color,” “connect every aligned color,” and “delete isolated noise” remain indistinguishable from the intended rule on positive-only data.

**Limitation.** The selected examples cover the nearest high-value precondition boundaries, not every possible multiplicity or non-aligned geometry.

## D7 — Exclude crossing and endpoint-overwrite scenes

**Choice.** Place connectable spans so they neither cross nor pass through another pair’s endpoint.

**Original rationale.** The imported generator attempted collision avoidance but did not state why. The Racket authority processes colors in sorted order, so crossings would introduce overwrite precedence not evidenced canonically.

**Alternatives considered.** Allow crossings and teach ascending-color priority; reject only endpoint collisions; add crossing as an explicit profile.

**Probe.** `analyze_grid` counts intersections and endpoint risk; `self_check` rejects either condition. All generated and canonical scenes pass.

**Failure mode avoided.** The dataset should not train a color-order rule that is merely an implementation artifact.

**Limitation.** A future canonical example may establish crossing semantics; until then, the generator remains silent.

## D8 — Keep difficulty semantic-neutral but layout-keyed

**Choice.** Easy, medium, and hard use the same profile schedule and exact canonical support, while the difficulty band participates in deterministic layout RNG.

**Original rationale.** The imported dimensions varied strongly by difficulty, which caused easy and hard to have zero canonical support.

**Alternatives considered.** Remove difficulty entirely; assign different profile weights; make hard scenes larger or crossing-heavy.

**Probe.** Repeated calls are deterministic; the same seed/profile yields distinct layouts across the three bands; every band remains 20/20 exact in profile-floor sampling.

**Failure mode avoided.** Difficulty labels become a spurious proxy for off-manifold dimensions or missing semantic branches.

**Limitation.** The bands differ in layout rather than proven conceptual hardness because the canonical set provides no defensible hardness calibration.

## D9 — Add a reusable curriculum auditor

**Choice.** Add `workspace/audit_curriculum.py` plus tests.

**Original rationale.** No task-specific reproducible probe existed outside the broad battery.

**Alternatives considered.** Rely only on the central battery; leave an ad hoc notebook; add another runtime hook.

**Probe.** Tests were written first and initially failed because the tool did not exist. The finished tool passes its CLI and report tests. A retained 100-seed run reports 1,200 generated cases, zero failures, balanced profile counts, and all five rivals refuted.

**Failure mode avoided.** Future edits can pass superficial generation tests while silently breaking schedule coverage, observability, or lesson identifiability.

**Limitation.** The tool audits declared rivals; it cannot prove that no undeclared shortcut exists.
