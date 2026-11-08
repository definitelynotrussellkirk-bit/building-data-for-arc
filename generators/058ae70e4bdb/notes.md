# Working notes: 058ae70e4bdb

Imported associated notes retain original evidence and timestamps in `evidence/associated_notes.jsonl`. The original rationale for version `2.0.1` is otherwise unknown; all statements below are measurements or decisions from this review.

## Baseline findings

The selected baseline had four reproducible blockers:

1. no pinned `RULE_HASH`;
2. an identity draw (`difficulty=easy`, seed/sample index `36`) where a wall merge destroyed the only fillable regions;
3. degenerate textures advertised as ordinary domain values;
4. an override surface that was not falsifiable and produced 3,303 override findings in the baseline battery.

Its random lesson assembly also lacked an executable semantic contract. Correct individual labels did not ensure that three demonstrations distinguished plausible shortcut rules.

## Repair decisions

- Pin the unchanged canonical authority with `RULE_HASH = "f3ddcec3d159"`.
- Replace the loosely coupled texture knobs with one exact, observable `scene_profile` axis.
- Preserve all five canonical `(height, width, palette-size)` profiles in every difficulty band.
- Use a deterministic three-profile semantic schedule so every consecutive three-example lesson carries the intended contrasts.
- Make every ordinary draw non-identity.
- Declare executable semantic witnesses and rivals rather than documenting them only in prose.
- Reject unknown override axes and verify requested profiles by re-observing the finished grid.
- Keep the selected Racket rule unchanged; Python `rule_mirror` is test support, not authority.

## Teaching design

`same_color_pair` intentionally bundles three distinctions in one scene: equal markers do not make a room ineligible, a two-color room does not fill, and a color may recur in another region. The two merged profiles then establish that connected-region palette—not rectangular room shape—controls the result. This redundancy keeps all hold-one-out rotations of four consecutive generated pairs distinguishable by the declared rivals.

The `rectangular_singleton_only` rival is a lesson competitor but not a canonical shortcut claim because it does not fit every authoritative canonical pair. `CANONICAL_SHORTCUTS` contains only rivals independently verified to fit all five canonical examples.

## Retained probes

`workspace/deep_audit.py` is a source-bound independent audit. It:

- parses regions and computes outputs without calling the generator mirror;
- exhausts every declared exact profile across all difficulty bands;
- checks replay, observability, strict support, non-identity, and canonical morphology;
- verifies every actual canonical-shortcut declaration against authoritative pairs;
- iterates the generator's actual `LESSON_COMPETITORS` over every held-out position of four-pair windows;
- records generator and audit-tool SHA-256 hashes in JSON.

The review stress run used 50 draws per profile per band and 100 cyclic starts per band: 900 unique profile inputs, 1,200 lesson rotations, 4,800 competitor checks, and zero failures.

## Known limits

This is not an exhaustive proof over all grids or all possible human shortcut rules. Support is intentionally narrow: the five canonical morphology profiles, a 2×3 compartment layout, three or four seed colors, zero to two markers per region, and at most one non-rectangular merged region. Difficulty changes deterministic morphology/layout randomness rather than rule complexity. A future expansion should add new exact profiles and witnesses before widening the advertised domain.
## Current reviewer considerations

Source SHA-256: `c927dd22bee82bdb174e4b2af1092a6e5e9b33f8021869d224e28c08ebb70487`.

# Decisions for 058ae70e4bdb

The imported version was `2.0.1`. Its detailed original rationale was not present in the selected notes; `evidence/associated_notes.jsonl` was empty. Baseline behavior and retained check evidence are therefore the only basis for describing the old design.

## D1 — Keep the canonical rule; repair only the generator contract

**Choice.** Keep the selected Racket authority unchanged and pin it with `RULE_HASH = "f3ddcec3d159"`.

**Why.** All five canonical pairs agree with the connected-region rule, and baseline authority sync/Racket lint passed. The defects were generation, validation, override, and lesson-design defects—not a rule-output disagreement.

**Alternatives rejected.** Changing the rule to fit the old rectangular-band implementation would narrow the task and invalidate punched-wall connected regions. Replacing the authority with the Python mirror would reverse the intended authority relationship.

**Probe.** The independent workspace oracle agrees with all five canonical outputs; final battery authority sync and rule smoke are green. `rule_mirror` is checked against the independent oracle and Racket in task tests.

**Failure mode / limitation.** Pinning proves source identity, not semantic completeness. A future authority update must deliberately update the hash and rerun canonical and generator evidence.

## D2 — Replace four loose axes with one exact semantic axis

**Choice.** Remove the old `grid_h`, `grid_w`, `n_bands`, and `texture` public controls and expose only `scene_profile` with six exact values.

**Why.** The old axes were not jointly falsifiable: degenerates overlapped ordinary values, many combinations were invalid, and the baseline override stage reported 3,303 findings across 23,130 draws. The new axis names a semantic scene that can be recovered from the returned grid.

**Alternatives rejected.** Declaring a large incompatibility matrix would preserve a complex surface with little training value. Keeping diagnostic degenerates in the ordinary axis would continue mixing invalid/no-rule examples with training data. Making every geometry knob public would recreate joint-support problems.

**Probe.** Task tests force every profile in every difficulty band, compare `observe_overrides` with the request, and require unknown-key rejection. Final override stage is green.

**Failure mode / limitation.** Exact profile observation is intentionally task-specific. Adding a new profile requires a unique observable signature and a profile witness; otherwise two labels may alias to the same grid semantics.

## D3 — Preserve the five linked canonical morphology profiles

**Choice.** Cycle through canonical `(height, width, total palette size)` triples: `(9,11,5)`, `(10,12,5)`, `(9,13,5)`, `(11,11,6)`, and `(10,14,5)`, with a band-specific offset.

**Why.** This preserves linked support rather than independently matching height, width, and palette marginals. Every band sees all five within its first 20 draws.

**Alternatives rejected.** Independent random height/width/palette draws can create unsupported combinations. Restricting to a single canonical profile would make profile-floor pass trivially while reducing morphology. Expanding beyond canonical shapes before semantic repair would mix two changes and make regressions harder to localize.

**Probe.** `strict_canonical_like`, task tests, profile-floor, and the 900-draw deep audit all require an exact canonical linked profile.

**Failure mode / limitation.** This is conservative support, not broad generalization. The generator does not currently cover every lawful wall topology or arbitrary grid size.

## D4 — Use a 2×3 compartment lattice with at most one punched wall

**Choice.** Build six rectangular rooms behind a complete color-8 border; merged profiles punch one separating wall cell to form one non-rectangular connected region.

**Why.** Six rooms provide enough space to co-locate positive and negative witnesses while retaining simple parsing. One punched wall supplies the key connected-component contrast without introducing multiple ambiguous mergers.

**Alternatives rejected.** The old variable band construction could produce identity cases and weaker lessons. Fully free-form walls greatly enlarge the validator and shortcut surface. Never punching a wall would permit a rectangular-room shortcut.

**Probe.** `self_check` enforces 4–9 regions and at most one non-rectangle; profile witnesses distinguish merged one-color from merged two-color scenes. The deep audit independently parses components.

**Failure mode / limitation.** A learner can still specialize to “mostly six rooms” or “at most one merge.” That is documented domain restriction, not evidence of universal connected-component generalization.

## D5 — Limit each region to zero, one, or two markers

**Choice.** Use zero markers for empty controls, one marker for ordinary fill cases, equal-color pairs for marker-count counterexamples, and two distinct colors for non-fill cases.

**Why.** These are the minimum constructions needed to distinguish distinct-color count from marker count while keeping examples visually legible.

**Alternatives rejected.** Three-plus markers add combinatorial variety but no new rule boundary for this task. Omitting empty rooms would erase an unchanged control. Omitting equal pairs leaves “exactly one marker” viable.

**Probe.** `self_check`, exact profile predicates, semantic witnesses, and declared rivals exercise all cases. Every ordinary draw contains at least one fillable region, preventing identity outputs.

**Failure mode / limitation.** The generator does not directly train larger same-color multisets or regions with more than two distinct colors; those remain lawful extrapolations rather than sampled support.

## D6 — Make the ordinary schedule semantic and deterministic

**Choice.** Cycle `same_color_pair → merged_two_color → merged_single_color` by `sample_index mod 3`, independent of seed and difficulty.

**Why.** Every consecutive three-example training lesson then contains the same complete teaching basis while seed and band still vary layout, colors, and canonical morphology. This removes the chance that three random examples jointly omit a decisive contrast.

**Alternatives rejected.** Pure random profile draws can produce correct but underdetermined lessons. Rejection sampling until a lesson happens to be identifiable is more expensive and makes replay/debugging less transparent. A longer schedule would require more demonstrations or leave some windows weak.

**Probe.** Task tests examine every consecutive three-demo window. The source-bound deep audit enumerates 100 cyclic starts per band and all four hold-one-out rotations of four-pair windows. Production lesson census independently materialized 300 lessons and 1,200 rotations with no ambiguity.

**Failure mode / limitation.** Deterministic schedules can be learned as position priors if assembly leaks sample index or sequence order. Match against the actual downstream shuffling/assembly policy before relying on the schedule outside this pipeline.

## D7 — Bundle multiple shortcut counterexamples into `same_color_pair`

**Choice.** In one rectangular scene include: an equal-color pair that fills, a two-color room that stays, a color repeated in another region, and an empty room.

**Why.** This gives each hold-one-out lesson redundancy. Even when one merged profile is the query, the remaining demonstrations still refute marker-count, fill-all-nonempty, and global-uniqueness shortcuts.

**Alternatives rejected.** Assigning one witness to one profile makes query rotation fragile. Treating empty-room preservation as a standalone semantic witness was rejected after the semantic gate correctly noted it had no linked declared rival; it remains a profile grammar property instead.

**Probe.** `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `PROFILE_WITNESSES`, the task tests, and the deep audit all check these predicates. The intermediate semantic-gate failure is retained in `checks/after-attempt-1/`.

**Failure mode / limitation.** A finite witness set can miss an undeclared shortcut. Witness/rival additions should be source-bound and accompanied by a minimized lesson counterexample.

## D8 — Declare four executable rivals and reject surviving lessons

**Choice.** Declare `exactly_one_marker`, `fill_every_nonempty_region`, `globally_unique_color_only`, and `rectangular_singleton_only`; use the first three as canonical-shortcut claims and all four as lesson competitors.

**Why.** The first three fit every canonical pair and therefore are especially dangerous. The fourth is invalidated by generated non-rectangular examples but does not fit all canonical pairs, so claiming it as canonical-compatible would be false.

**Alternatives rejected.** Prose-only rival lists are not regression tests. Copying rival names into a workspace tool risks drift; the tool imports the actual declarations. Claiming uniqueness over all conceivable rules would be unsupported.

**Probe.** The deep audit independently verifies 15 canonical shortcut claims (3 rivals × 5 pairs), then runs 4,800 competitor checks across 1,200 rotations. `lesson_identifiable` independently reports any survivor in the production census.

**Failure mode / limitation.** Passing a finite named set establishes only that those rivals are ruled out. It is not a proof that every human- or model-plausible hypothesis is eliminated.

## D9 — Build a source-bound independent audit tool

**Choice.** Add `workspace/deep_audit.py` and a task test that executes a small portable run.

**Why.** Future agents need a one-command check that does not trust the generator's own mirror, copied rival lists, or prose counts. The tool records source and tool hashes in JSON.

**Alternatives rejected.** Ad hoc notebook/manual checks are not replayable. Calling only `self_check` and `rule_mirror` could make implementation and oracle share the same bug.

**Probe.** A deliberately missing tool first caused 1 of 35 tests to fail (`checks/task-tests-deep-audit-red/`); after adding it, 35/35 passed. The stress run checked 900 unique exact-profile inputs and 1,200 lesson rotations with zero failures.

**Failure mode / limitation.** The audit shares some semantic declarations with the generator by design, so a missing rival declaration remains invisible. Its output must be read as source-bound finite evidence.
