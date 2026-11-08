# Current notes: ad92d10d919c

## Intended rule and authority

A zero interior cell is filled with color `v` exactly when its four diagonal neighbors are all the same nonzero color `v`. The selected Racket authority was not changed. The generator pins `RULE_HASH = "2fadbb67030c"`; final generator SHA-256 is `c58bf9b69b5aad40ea5f186d1bd46ed4b9ae57d04ff98d458955f09f2ebc2f27`.

## Repaired distribution

Version `3.0.0` constructively places `1..3` positive X motifs in separated 3×3 slots and adds exactly one scheduled negative control:

- even `sample_index`: a three-of-four same-color near-miss;
- odd `sample_index`: four nonzero diagonals split 2+2 across two colors.

The schedule period is 2. Lessons use three demonstrations plus one query. The two controls refute the canonical-fitting shortcuts `at_least_three` and `any_four_nonzero`; both shortcuts fit all four canonical pairs.

The public exact controls are now only `grid_h=6..16`, `grid_w=7..18`, and `motif_count=1..3`. Unknown keys, malformed scalars, out-of-range values, and invalid difficulties fail loudly. A separated-slot constructor guarantees the requested positive motif count rather than sampling centers and silently dropping collisions. Minimal retained regression: `counterexamples/exact-count-drop-seed2.json` shows the old `6×7, motif_count=3` request produced 2 positive motifs while the repair produces 3.

## Validation and semantic contract

`self_check` now verifies rectangular ARC cells, allowed dimensions, recognized positive/partial/mixed motif structure, pairwise-disjoint 3×3 neighborhoods, exact ownership of every nonzero cell, and exactly one scheduled negative control for ordinary samples. `strict_canonical_like`, `observe_overrides`, executable witnesses/rivals, and `lesson_identifiable` are source-bound hooks.

The mixed-control half is intentionally anchored to a canonical `6×8` profile with one positive motif and one diagonally separated mixed control. This supplies exact profile/object support; the partial-control half retains broad size/count variation. The final profile floor measured 33/60 exact and 41/60 envelope hits, with exact support in easy/medium/hard. Strict canonical-like support was 532/600 (88.7%).

## Final evidence

- Full after battery: 12/12 green — `checks/after-final/result.json`.
- Portable selected-task tests: 51/51 — `checks/task-tests-final/result.json`.
- Random lesson census: 300/300 production lessons and 1,200/1,200 query rotations, zero ambiguity/errors against the two declared rivals — `checks/lesson-census-final.summary.json`.
- Fixed-seed period census: 6 lessons, 24 pairs/rotations, zero ambiguity/errors — `checks/schedule-period-s0.summary.json`.
- Parametric prototype: episode-level `required_matches ∈ {3,4}`; threshold 4 is the exact canonical program, all labels/rivals execute through Racket, and every demonstration refutes the other setting — `workspace/parametric/` and `checks/parametric/gallery/report.json`.
- Fresh exposed solve: first attempt passed all 3 visible demonstrations; earlier rule exposure declared `yes`, reference consultation `no` — `solve/summary.json`.

## Known limits and open findings

The lesson evidence is finite and only proves the checked declarations; it is not universal identifiability. The broad random census does not enumerate every seed, and the complete schedule-period census uses one fixed seed. Generic mutation rivals are diagnostic rather than a principled exhaustive hypothesis class. The parametric threshold-3 rule is a proposal only and is not part of canonical execution or training approval.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-361d29beeb4e7c05:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `01fd4c1b8afc5aa6425149e1d60cb0ad4ee9950903cffc0ec77036ec170cfa0a`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused repair-bound closure ofold01fd4c1b8afc5aa6425149e1d60cb0ad4ee9950903cffc0ec77036ec170cfa0a againstcurrentc58bf9b69b5aad40ea5f186d1bd46ed4b9ae57d04ff98d458955f09f2ebc2f27. Owner staticinspection confirms _center_slots constructsdisjoint3x3capacity,_choose_slots samplesexactmotif_count+1 andpaintsallrequestedpositivespluspartial3/mixed2+2negativecontrol. Minimum6x7hasfour slots;seed2count-drop counterexample andthree-of-four-shortcut.json retained. Focusedtestscoverjoint6x7/count3,scheduledpartial/mixedcontrols andallcyclicquerypositions. Reviewer51portable/freshreplaytests,300lessons/1200rotations andseed0period2sixlessons/24rotations directlyexercisebothpriorunderfill andcanonical-fittingthree-cornercoveragegap. Not genericacceptance/sourceeditclosure;finite shapes/rivals/seeds,notownerRacket rerun.

### Assessment or prior finding

## ad92d10d919c

**Version/source:** 2.0.1;
`01fd4c1b8afc5aa6425149e1d60cb0ad4ee9950903cffc0ec77036ec170cfa0a`.
Normalized rule hash: `2fadbb67030c`.

**A1a — Reproduced shortcut gap.** The rival “fill a zero center when at least
three of its four diagonal neighbors agree on a nonzero color” fits all four
usable canonical pairs and all 300 sampled default inputs. Samples are seeds
0–99, sample index 0, in each of easy/medium/hard; all 300 inputs are unique.
The intended rule requires four matching diagonal neighbors, not merely three.

An exact discriminator is already available through the advertised override
`texture=partial_xs`, seed 0, sample 0, easy. Its first incomplete motif has color
4 at (2,2), (4,2), and (4,4), with (2,4) absent. The intended Racket output leaves
(3,3) zero; the rival paints it 4. A second incomplete motif gives the same kind
of discrepancy. The input passes the target's validator and is in its explicitly
advertised degenerate domain, but ordinary defaults never select that branch.
This is a **sampling/lesson coverage finding**, not a wrong Racket label.

**A1b — Reproduced exact-count defect.** In 100 easy draws, seeds 0–99, sample 0,
with `grid_h=6, grid_w=7, motif_count=3`, **26/100** silently emit fewer than three
motifs. Three disjoint 3×3 neighborhoods fit this canvas (for example centers
(1,1), (1,4), (4,1)), so the requested count is feasible. Seed 2 is the retained
counterexample: two motifs, validator returns `[]`, no explicit rejection.
Random sequential placement exhausts its 300 tries for a later motif and continues
without reporting the omission. The actual Racket output is otherwise lawful.

**What was checked:** 304 public Racket comparisons (four canonical pairs plus
300 defaults) agree with a separate diagonal-consensus implementation, with no
reference errors and no oracle mismatches. The two counterexamples were then
rechecked with the supported `arcpuzzles apply` command. No broader distribution
or complete-lesson guarantee was proved for this audit.

**Evidence:** `checks/audit/ad92d10d919c/summary.json`, `canonical-fit.json`,
`count-drops.json`, `counterexamples.json`, `racket.json` and `racket-receipts.jsonl`.
**Proposed follow-up:** make count placement constructive or explicitly reject;
include complete and incomplete diagonal motifs within ordinary lessons.
**Patch status:** findings only; unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-361d29beeb4e7c05-v0001/audit_assets.json), manifest SHA-256 `512d5b20a6d9105b32ff510168cb964973c59550f607652e3c218c0bb393a85d`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `c58bf9b69b5aad40ea5f186d1bd46ed4b9ae57d04ff98d458955f09f2ebc2f27`.

# Decisions: ad92d10d919c

## D1 — Preserve the canonical Racket authority

**Prior state:** the generator omitted `RULE_HASH`, but rule smoke and canonical examples showed the selected authority already implemented the intended four-diagonal consensus rule.

**Decision:** pin `RULE_HASH = "2fadbb67030c"` and leave both canonical data and selected Racket source unchanged.

**Alternatives considered:** rewrite the rule, synchronize an equivalent new formulation, or leave the hash absent. No behavioral rule defect was reproduced, so any rule rewrite would increase review scope without training value. Evidence: final rule-smoke and authority-sync stages; the selected authority file still has baseline SHA-256 `38dab21d5374c99beb408a13874182b8fddd8e0c9e2fda48cfcc648471b2dedd`.

**Limit:** pinning detects drift but does not prove the authority is correct outside the canonical and generated domains.

## D2 — Replace broad dishonest controls with three exact observable axes

**Prior state:** the generator declared palette kind/size, position bias, distinct-color count, density, and texture controls. Several were dead, aliases, conditionally ignored, or impossible to infer from returned pixels. Unknown overrides were accepted and legal requests could be clamped or underfilled.

**Decision:** expose only `grid_h=6..16`, `grid_w=7..18`, and positive `motif_count=1..3`. Reject unknown axes, booleans, floats, strings, explicit `None`, out-of-range values, negative indices, invalid difficulties, and non-integer seeds/indices.

**Alternatives considered:** preserve approximate controls, declare a large incompatibility matrix, or add exact palette/control-orientation axes. Approximate controls violate the exact API contract; a compatibility matrix would hide the core capacity defect; exposing curriculum-owned negative controls would make users able to erase teaching coverage.

**Evidence:** baseline override stage failed; final override stage has no findings/warnings. Task tests cover joint endpoint combinations in every band.

**Limit:** callers cannot force control type, colors, or orientation. Those are intentionally sampler-owned nuisance variables.

## D3 — Construct exact motif capacity before painting

**Prior state:** random center proposals were rejected when 3×3 neighborhoods collided. The loop could exhaust candidates and silently emit fewer motifs than requested. Seed 2 with `6×7, motif_count=3` reproduced 2 instead of 3.

**Decision:** enumerate a 3-spaced lattice of disjoint center slots and sample `motif_count + 1` slots: exactly the requested positive motifs plus one negative control. The minimum canvas has four slots, so all declared combinations are constructive.

**Alternatives considered:** increase retry counts, resample the whole grid, or mark small-grid/high-count combinations incompatible. Retrying remains probabilistic; whole-grid rejection makes exact controls fragile; incompatibility is unnecessary because a constructive layout exists.

**Evidence:** `counterexamples/exact-count-drop-seed2.json`; focused exact-control tests; final override and distribution gates.

**Limit:** the lattice narrows relative motif positions. Broad canvas/count variation and random slot selection remain, but arbitrary overlapping or adjacent motifs are outside the declared domain.

## D4 — Teach both canonical-fitting shortcuts in every complete lesson

**Prior state:** all canonical pairs contain only complete same-color X motifs. Therefore both `at_least_three` and `any_four_nonzero` fit every canonical label. Ordinary baseline generation did not guarantee counterexamples, so a lesson could be label-correct yet teach either shortcut.

**Decision:** declare a period-2 curriculum. Even sample indices contain exactly one three-corner same-color near-miss; odd indices contain exactly one four-corner 2+2 mixed-color near-miss. Use three demonstrations plus one query. Declare executable witnesses, rivals, canonical shortcuts, lesson competitors, and a leave-one-out `lesson_identifiable` hook.

**Alternatives considered:** random negatives, only partial negatives, only mixed negatives, or more demonstrations. Random negatives can disappear from a lesson; either negative alone leaves one shortcut; four demonstrations increase tokens without improving the two declared distinctions.

**Evidence:** both rivals fit 4/4 canonical pairs; the semantic gate checked 60/60 witness/rival claims for each negative type; random census passed 300 production lessons and 1,200 rotations; fixed-seed period census passed 6 lessons and 24 rotations.

**Limit:** the declared rival set is finite. It does not establish universal uniqueness of the intended program.

## D5 — Anchor half the schedule to a canonical profile, retain variation in the other half

**Intermediate result:** the first semantic repair was correct but failed coarse object/profile gates. Random broad shapes gave zero exact easy-band profile hits, and coarse four-connected component counts diverged from canonical support.

**Decision:** when no exact overrides are supplied, the mixed-control half uses `6×8`, one positive motif, and a diagonally separated mixed control. This gives palette size 3 and eight isolated nonzero components. The partial-control half keeps broad weighted `grid_h`, `grid_w`, and motif-count support.

**Alternatives considered:** lock every sample to canonical shapes, game the object counter with connected controls, or relax the profile gate. Locking all samples sacrifices useful variation; connecting motifs changes the visual task; relaxing shared gates is outside task scope.

**Evidence:** final profile floor is 33/60 exact and 41/60 envelope, with exact hits in all bands; strict canonical-like support is 532/600. `test_mixed_schedule_is_a_canonical_profile_and_matches_coarse_authority_structure` protects the design.

**Limit:** odd-index default samples are intentionally less diverse. Explicit overrides still support the full legal axis domain on either schedule residue.

## D6 — Make `self_check` a structural domain validator

**Prior state:** validation mostly checked rectangularity and the existence of any nonzero cell. Blank-like or unrelated colored structures could pass, and motif count/ownership was not verified.

**Decision:** parse every zero center's diagonals, recognize positive, partial-3, and mixed-2+2 motifs, require pairwise-disjoint 3×3 neighborhoods, require every nonzero cell to be owned exactly once, enforce positive count 1..3, and enforce exactly one scheduled control for ordinary generated inputs.

**Alternatives considered:** use only a prediction-equality check or keep a permissive rule-domain validator. Output equality cannot prove intended input structure; a permissive validator lets distribution defects hide behind an executable rule.

**Evidence:** malformed/impostor mutation tests; all canonical pairs accepted; final self-check and defect-lint stages green.

**Limit:** the validator describes the selected training manifold, not every grid on which the Racket rule has defined behavior.

## D7 — Add an independent diagnostic probe

**Decision:** add `workspace/reference_probe.py` to classify centers, observe axes, and implement the two rivals without importing generator helpers. Production labels remain Racket-owned.

**Alternatives considered:** test only generator-internal helpers or call Racket for every small assertion. Internal-only tests can share implementation bugs; Racket-only tests are slower and obscure structural failures. The final design uses an independent Python probe for structure and source-bound Racket checks for authority.

**Limit:** the independent probe can still share a conceptual misunderstanding; canonical labels and public Racket execution are the backstops.

## D8 — Prototype only one small episode-level rule parameter

**Decision:** assess `required_matches ∈ {3,4}`. Setting 4 returns the exact canonical program. Setting 3 fills when one nonzero diagonal color appears at least three times. The value is fixed once per episode, and complete-X, partial-3, and mixed-2+2 fixtures make every demonstration distinguish the two settings.

**Alternatives considered:** parameterize color agreement, center occupancy, neighborhood type, or per-example thresholds. Those either alter several semantics at once, are poorly identified by compact demonstrations, or violate the “choose once per episode” requirement.

**Evidence:** six prototype tests pass; two materialized Racket episodes cover both settings; every demo and query differs under the other setting; canonical setting has program SHA-256 `2fadbb67030c4aa009208317f548ae0019b1bf96b23915403b1c114e6719546f`.

**Status and limit:** proposed prototype only. It is not wired into canonical generation, catalog approval, or training admission. Evidence covers controlled fixtures and two retained seeds, not arbitrary generated episodes.

## D9 — Keep failed iterations and solve exposure honest

The initial after battery is retained under `checks/after/`; it failed the object/profile and schedule-enumeration gates. The final passing rerun is separate under `checks/after-final/`. The post-repair solve was prepared from final generator bytes and passed 3/3 visible examples on revision 1. Because the rule had already been read during repair, `earlier_rule_exposure=yes`; no generator, Racket source, private labels, or reference explanation was consulted during the solve phase.

## D10 — Leave the two audit targets unchanged

The assigned adversarial targets were findings-only. `b09f5ee22328` retains a canonical plurality input rejected by its strict-majority validator. `b88894a36787` retains a lawful horizontal reflection with missing interior header index 1, absent from sampler support, where a geometry-based shortcut fails. Both were freshly reproduced with public Racket receipts and no target source edits.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/ad92d10d919c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
