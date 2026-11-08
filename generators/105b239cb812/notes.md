# Current notes: `105b239cb812`

## Intended rule

Split an `n x (3n+2)` input at the two full color-5 columns into square panels A, B, and C. Infer the first unique transform in authority order—`cw`, `180`, `ccw`, `lr`, `ud`, `transpose`—that maps the **complete** panel A to B, then apply it to C.

Pinned authority: `RULE_HASH = aa699e35aade`. The Racket rule and canonical examples were not changed in review `review-0bb5cf551818a26c`.

## Reversal of the prior generator decision

Baseline version 2.1.1 (SHA `753f6bd21b61acd390bc32751fcf5f97e83d72e90b1dba3446885ef620409ce9`) transformed normalized foreground coordinates and independently repositioned A and B. That did not implement the whole-panel equality tested by the authority. The prior return `review-62482c684f7c40f3:v0001` was used as a lead; its core mismatch was independently reproduced.

Version 3.1.0 instead paints A first and derives B by a literal transform of the complete panel. Candidate motif placements are accepted only when identity plus all six authority transforms are pairwise distinct, so each A→B relation is unique.

## Current sampler contract

- sizes 4–7 in every difficulty band; every fourth default sample is a canonical 4×14 profile;
- exact axes: `panel_size`, `transform`, `shape_kind`;
- shape kinds are connected 4-, 5-, and 6-cell motifs;
- unknown/invalid overrides and non-literal or negative sample indices are rejected;
- `observe_overrides`, `strict_canonical_like`, `rule_mirror`, semantic witnesses/rivals, `schedule_profile`, and `lesson_identifiable` are executable;
- three demonstrations per lesson;
- cyclic transform schedule `cw,180,ccw,lr,cw,ud,ccw,transpose`.

The schedule deliberately places two quarter-turns in every four-pair window. An intermediate two-demo design allowed `reverse_pair` to fit all rotated demonstrations and change the query; the compact source-bound witness is `counterexamples/review-0bb5cf551818a26c/directional_lesson_ambiguity.json`.

## Final evidence

Final generator SHA: `23d2ff60b89eb176b82c1030a5bb111a218cf50bef4b11e766c94936409c1c3a`.

- 241 task-local tests passed.
- All 12 official after stages passed standalone.
- Fixed-seed schedule enumeration: 24 lessons / 96 rotations, zero declared-rival ambiguity or hook/scoring errors.
- Production census: 300 lessons / 1,200 rotations, zero declared-rival ambiguity or hook/scoring errors.
- Post-repair visible solve is bound to the same generator hash and passed all visible examples.

The aggregate controller attempt under `checks/after-v2/` was interrupted at its defect-lint transition and is retained as an incomplete run; it is not treated as an aggregate pass. The same stage and all other stages passed in standalone source-bound runs.

## Known limits and open status

The transform schedule over-samples quarter-turns to guarantee direction evidence. Motifs are sparse, connected, single-color shapes; dense, disconnected, multicolor, and larger-panel cases are outside this sampler. The semantic census evaluates declared finite competitors and does not prove universal identifiability.

The historical audit in `evidence/review_index.json` remains administratively unresolved until maintainer integration independently verifies this repair; these notes do not rewrite retained review history.
## Current reviewer considerations

Source SHA-256: `23d2ff60b89eb176b82c1030a5bb111a218cf50bef4b11e766c94936409c1c3a`.

# Decisions for `105b239cb812`

## D1 — Treat transforms as operations on the complete square panel

**Prior choice.** Version 2.1.1 normalized foreground coordinates, transformed that cropped motif, and independently sampled A/B offsets.

**Decision.** Panel B is now computed by applying the selected transform directly to the complete panel A array.

**Why.** The authority compares entire panels. The prior representation made six of eight advertised controls fail to produce the relation the rule was asked to infer. Literal panel transforms remove the representation mismatch rather than teaching the validator to excuse it.

**Rejected alternative.** Constrain the two independent placements so their offsets happen to transform consistently. This is equivalent in outcome but has more coupled state and more ways to drift from the authority.

**Probe/failure mode.** Every generated pair is independently split and checked for exactly one whole-panel match; `rule_mirror` is compared with the selected authority in rule-smoke tests.

## D2 — Expose only the six transforms selectable by the pinned rule

**Prior choice.** The generator advertised identity and anti-transpose in addition to six transforms.

**Decision.** The exact transform domain is `cw|180|ccw|lr|ud|transpose`, in canonical rule order.

**Why.** Identity and anti-transpose are not selectable branches of the pinned authority. Advertising them created mislabeled controls even when their geometry was otherwise valid.

**Rejected alternative.** Modify the Racket rule to add the two branches. The canonical examples and pinned rule already define a coherent six-transform task; changing authority would expand scope without evidence that this was intended.

**Limitation.** This generator does not train identity or anti-transpose generalization.

## D3 — Use a unique identity-plus-six-transform orbit

**Prior choice.** “Chiral” base shapes were assumed to make transform inference unique, but placement and panel symmetry were not checked against the full authority.

**Decision.** Candidate placements are retained only when identity and all six authority transforms yield seven distinct complete panels.

**Why.** Uniqueness is now a constructive property of each sampled input, not a shape-name assumption. It also guarantees panel C changes under every legal transform, making copy-query a concrete rival rather than a vacuous label.

**Rejected alternative.** Sample freely and retry after validation. Precomputing deterministic candidate sets is simpler, reproducible, and avoids hidden rejection bias.

**Limitation.** The candidate library contains connected sparse motifs only; dense or symmetric structures are intentionally excluded.

## D4 — Reduce the override surface to exact, observable task controls

**Prior choice.** Eight axes included aliases, fixed-value metadata controls, palettes, and deliberately degenerate textures; several were dead, overlapping, or authority-invalid.

**Decision.** Keep three semantic axes: `panel_size`, `transform`, and `shape_kind`. Reject unknown keys and invalid values, and expose `observe_overrides` for all three.

**Why.** Each retained axis changes a measurable property while preserving the task. Degenerate examples belong in validators/counterexamples, not the lawful training sampler.

**Rejected alternative.** Preserve legacy axis names as no-op compatibility aliases. Silent aliases make misspellings and dead controls look successful.

**Probe/failure mode.** The task suite enumerates every difficulty × size × transform × shape combination and verifies exact observation and authority behavior.

## D5 — Preserve canonical scale without making difficulty a legality boundary

**Prior choice.** Difficulty changed the legal draw interval, so values advertised as globally valid could be rejected in particular bands; hard also lacked canonical 4×14 support.

**Decision.** All sizes 4–7 are exact-override legal in every band. Every fourth default sample is size 4; difficulty changes only the non-anchor mixture.

**Why.** This separates curriculum weighting from override legality and guarantees a canonical-size/palette hit in each band's fixed profile-floor sample.

**Rejected alternative.** Restrict hard to 6–7 and declare band-specific incompatibilities. That would preserve a needless train/evaluation gap and complicate exact controls.

**Limitation.** The deterministic anchor introduces a sample-index correlation. Non-anchor draws and exact controls provide all sizes, and the final distribution/override gates passed.

## D6 — Use three demonstrations and an eight-step direction-safe schedule

**Intermediate choice.** Two demonstrations with a balanced-looking schedule passed ordered lesson checks but failed query rotations: a rotated lesson could leave two self-inverse demonstrations and a quarter-turn query, so B→A and A→B were indistinguishable.

**Decision.** `EXAMPLES_NEEDED = 3` and the cyclic schedule is `cw,180,ccw,lr,cw,ud,ccw,transpose`.

**Why.** Every four consecutive pairs contain two directional quarter-turns. Holding out any one pair leaves at least one quarter-turn demonstration, which refutes `reverse_pair` for asymmetric motifs.

**Rejected alternatives.** A uniform six-step cycle with three demos has unsafe windows. More demonstrations could repair it but increases lesson cost. Random resampling until a witness appears hides the curriculum contract and complicates reproducibility.

**Measured support.** Fixed-seed exhaustive schedule census: 24 lessons and 96 rotations, zero ambiguity. Wider census: 300 lessons and 1,200 rotations, zero ambiguity.

**Limitation.** Quarter turns are over-represented (50% total). This is an intentional identifiability tradeoff, not a claim of uniform transform frequency.

## D7 — Declare executable witnesses, rivals, and lesson-level identification

**Decision.** Add `query_changes`, `quarter_turn_direction`, `copy_query`, `reverse_pair`, and `lesson_identifiable` hooks; declare the same rivals as lesson competitors.

**Why.** Pairwise label correctness does not establish that a lesson teaches the intended direction. The hooks make the relevant shortcuts executable and let the census retain exact counterexamples.

**Rejected alternative.** Describe rivals only in comments. Text cannot be source-bound, scored, or regression-tested.

**Limitation.** Passing a finite rival set is not a proof of unique induction among all possible programs.

## D8 — Validate the sampler boundary explicitly

**Intermediate defect.** Python booleans are integers, and the early repair also admitted negative indices.

**Decision.** `generate` and `schedule_profile` require `type(sample_index) is int` and `sample_index >= 0`; malformed overrides likewise reject booleans where integers are required.

**Why.** Sample index participates in deterministic curriculum scheduling. Alias values such as `True == 1` or negative residues can silently duplicate or rotate lessons.

**Probe.** A red/green regression covers `True`, `False`, `-1`, `1.0`, and `"1"`.

## D9 — Leave the Racket authority and canonical examples unchanged

**Decision.** Pin `RULE_HASH = "aa699e35aade"`; change only generator, task tests, task documentation, and a compact task counterexample.

**Why.** The defect was in the sampler's representation and curriculum, not in the canonical transformation rule. Final authority-sync and rule-smoke receipts pass on unchanged authority bytes.

## 2026-10-24 native parametric reviewer return

The task-local native adapter in `workspace/parametric/` adds one episode-fixed
parameter, `application = direct|inverse`. `direct` returns the exact canonical
Racket program byte-for-byte. Both settings first infer the unique complete-panel
A-to-B transform and then apply either that transform or its inverse to panel C.
The adapter supports 2–6 demonstrations and exactly four controller-side queries;
public projections expose one query at a time and omit settings, programs, future
queries, and private answers.

The generated family reaches a substantive 9x29 input. A 30x30 input is not lawful
for this three-square-panel grammar: width is `3*n + 2`, so `n=9` gives 29 columns
and `n=10` gives 32. The maximum case uses all available panel area rather than
padding a smaller puzzle.

A protected-Racket teaching audit exercised direct and inverse settings at seeds
5 and 23 with 2 and 6 demonstrations, four distinct queries, and seven finite
rivals. An initial version exposed a real crop-local shortcut because every C
panel touched all four borders; the sampler was repaired to include strict
sub-box placements and the crop-local direct/inverse rivals were added. The final
audit ran 322 Racket evaluations and retained only the selected setting in every
job. The causal witness substitutes `180` for an input-inferred `cw` transform and
changes the final output.

Native qualification at seeds 0 and 17 passed four jobs across both settings.
This return is reviewer-ready only: exact-source owner integration, fresh native
qualification, acceptance, and any training admission remain pending.

