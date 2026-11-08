# Working notes: f7c20cfd443f

## Current parametric proposal (October 24)

The separate `workspace/parametric/` family is reviewer-ready and native-qualified;
owner exact-source acceptance remains pending. The production generator and
canonical authority were not edited. `selection=all` now returns byte-for-byte
the formatted canonical-ledger program from task-local `canonical.rkt`, rather
than the semantically equivalent compact archival spelling. The first native
qualification exposed this binding mismatch; the corrected ledger regression
passes and the final qualification succeeds.

The alternative fixed settings keep all largest or all smallest four-connected
regions **after** clipped halo dilation. This requires the actual newly merged
regions and their areas. A protected wrong-order witness selects the tied
singleton input objects first and produces different final grids for both
alternate settings: `WORK/checks/f7c20cfd443f/causal/witness.json`.

Two constructive demos jointly reject the declared morphology/connectivity,
area-vs-bbox, new-cell-count, seed-count, premature-selection and tie shortcuts.
A default third demo retains the 9x9 source-scale anchor. Counts are 2..6 demos
(default 3) and 1..4 queries (normally 4), independent of each other. Identical seed
requests share inputs across settings. The extension permits 7..30 dimensions
and more isolated seeds; canonical production distribution is unchanged.
Four query profiles culminate in 55..75 seeds across 30x30. An observed seed 1
first-query collapse was repaired with an input-only retry requiring competing
component sizes, preserving single-query/four-query first-turn equality.

Current evidence: 24 focused tests; 108/108 bounded sampler episodes; 162 protected
Racket evaluations covering 6 episodes, 54 declared-rival cases and 7x7/30x30 bounds;
native qualification covers 3 settings × 2 seeds and 42 pair labels (78 executions with
setting rivals). No finite rival survived the first two demos in the audit.
The task-local `audit_family.py` reproduces checks and emits one-query public
files named only by visible-byte hashes, with all control data kept private.
See `workspace/parametric/evidence/bound/audit.json`, its native manifest, and
`WORK/checks/f7c20cfd443f/qualification/`.

Limits: finite rivals/seeds only, no learning-gain claim or training admission;
later queries may lawfully have a single merged region or tied areas. Broader
production batteries were not rerun for this prototype-only change. Earlier
missing-Racket statements below describe historical production evidence; this
prototype's retained labels were executed with the bundled protected runtime.
Next owner action: integrate the exact delta, then native-qualify and accept it.

## Selected rule and immutable authority

The canonical Racket rule is a clipped 3×3 dilation of every gray (`5`) input cell, with blue (`1`) output and black (`0`) elsewhere. Its assigned rule hash is `89548e944e39`. The canonical implementation matched all three available train/test pairs and was not changed.

## Baseline findings

The imported v2.0.0 generator had several independent data-quality defects:

- It omitted the required `RULE_HASH`.
- Default dimensions ranged from 4×4 through roughly 24×24, yet none of the pinned 60 draws matched the canonical `(9,9,2)` profile.
- The median generated object count was `1.0` versus canonical `3.5`.
- Multi-cell domino/L/2×2/plus “markers” changed the canonical singleton-object grammar and made the intended unit of transformation less clear.
- Several declared axes were unprobeable or constant, while unknown override keys were silently accepted.
- `self_check` accepted adjacent gray cells and inverted foreground/background scenes.
- No task-linked semantic contract or named shortcut counterexample existed.

Baseline battery: 4 green, 2 advisory, 6 failed. The rule-smoke, strict defect, and authority-execution checks were also blocked by the review host's missing Racket executable.

## Distribution decision

Use a four-step schedule keyed by `sample_index % 4`:

- `canonical_anchor`: canonical macrocell-center placement, nonoverlapping halos;
- `off_lattice`: interior, nonoverlapping singleton seeds with at least one seed outside the canonical lattice;
- `edge_clip`: at least one border seed, with no halo-overlap confound;
- `overlap`: interior seeds with one required Chebyshev-distance-two pair, while any extra seed stays separated.

The profiles isolate one decisive counterexample at a time rather than letting edge clipping and halo overlap occur accidentally in every profile.

Dimensions are scheduled by difficulty. Every band contains two exact 9×9 profiles per four-example cycle and two controlled extrapolation profiles. Across all bands, ordinary draws span both public bounds (`7` and `15`) without returning to the baseline's extreme 4..24 drift.

Default seed counts remain three or four, matching canonical object-count mass. The exact override range is one through four because a single seed is mathematically lawful and useful as a diagnostic, although ordinary lessons never use it.

## Semantic contract

The generator now exposes:

- `strict_canonical_like` and `MIN_STRICT_FRAC = 1.0`;
- a Python `rule_mirror` pinned against every canonical pair;
- five named rivals: aligned macrocell fill, ignore clipped edge seeds, expand only nonoverlapping seeds, preserve gray centers, and orthogonal-plus dilation;
- witnesses with explicit rival claims;
- `CANONICAL_SHORTCUTS` for the three wrong rules that fit every public pair;
- `lesson_identifiable`, which requires four demonstrations and rejects a lesson if any named rival survives;
- a declared four-profile schedule.

## Overrides and invariants

Only `grid_h`, `grid_w`, and `n_seeds` are public axes. All are exactly recoverable from the emitted grid through `observe_overrides`. Unknown keys and unknown difficulty labels raise `ValueError`. Every tested Cartesian boundary combination is valid, so no incompatibilities are declared.

`self_check` now rejects malformed/ragged grids, non-ARC values, dimensions outside 7..15, colors outside `{0,5}`, absent background or seed colors, seed counts outside 1..4, and any pair of 8-neighboring gray cells.

## Retained task-local tooling

`workspace/audit_curriculum.py` provides a Racket-free review aid. It pins the Python mirror to canonical pairs, audits profile isolation and distribution statistics, and checks every sliding lesson window against all named rivals. It explicitly states that it does not replace the protected Racket gates.

## Evidence and limitations

Focused tests cover canonical parity, schedule mass, profile isolation, lesson identifiability, witness/rival claims, override boundaries, determinism/freshness/global-RNG purity, and destructive grammar mutations.

The final review host had no `racket` executable, and outbound DNS prevented installing one. Therefore canonical Racket execution, rule-smoke timing, strict rule-dependent defect detectors, and execution-parity authority sync remain environment-blocked rather than claimed as passed. Static Racket lint did pass in the baseline and the selected Racket source was not modified.

The required after battery completed with **7 green and 5 failed stages**. `selfcheck`, `dist_gate`, `profile_floor`, `diversity`, `override`, `grammar`, and static `racket_lint` were green. `lint`, `rule_smoke`, strict `defect_lint`, `semantic_gate`, and `authority_sync` all recorded the same missing-Racket dependency. The inherited diversity stage's green status is not considered affirmative evidence because its log reports no materialized pairs.
## Current reviewer considerations

Source SHA-256: `0c57e5c118779b64a2257eff67976a71b18b19401652ad329c83a2ecab6dd3e8`.

# Decisions: f7c20cfd443f

This ledger records each material input-distribution choice, what the imported generator appeared to be trying to do, alternatives considered, the probes used, and known limitations.

## 1. Canonical Racket rule

**Choice.** Keep the selected Racket authority unchanged and pin the generator to rule hash `89548e944e39`.

**Original rationale.** The imported source described the same Chebyshev-radius-one dilation, but did not declare the required hash. The exact historical reason for omitting the pin is unknown.

**Alternatives considered.** Rewrite the rule; add special cases for the canonical lattice; replace it with a macrocell-fill rule.

**Probes.** Read the preserved Racket source and all train/test pairs. Implemented an independent Python mirror and required exact equality on every pair.

**Failure modes.** A Python mirror can repeat the same misunderstanding as the reviewer. This is why it is pinned to canonical examples and labeled non-authoritative.

**Limitations.** The host lacked Racket, so executable parity remains to be rerun elsewhere.

## 2. Input palette

**Choice.** Restrict all inputs to black `0` and gray `5`.

**Original rationale.** v2.0.0 had already removed an older random-background/decoy-color design after recognizing that it contradicted the canonical clean palette.

**Alternatives considered.** Reintroduce decoy colors; vary the seed color; vary the background while translating the rule.

**Probes.** Canonical palette inspection, profile-floor census, self-check mutation tests.

**Failure modes.** Extra colors would invite irrelevant color-conditioned shortcuts and no longer match the selected Racket rule, which responds specifically to `5`.

**Limitations.** Palette invariance reduces visual variety, but that variety would be semantically false for this task.

## 3. Seed object grammar

**Choice.** Use isolated singleton gray cells only.

**Original rationale.** The imported generator intentionally added domino, L, 2×2, and plus markers because the mathematical dilation can process any 5-region. That rationale was explicit, but it broadened the object grammar beyond every canonical input.

**Alternatives considered.** Keep all multi-cell shapes; retain them only in hard mode; allow connected shapes through an override.

**Probes.** Canonical component inspection, baseline object-count drift, destructive adjacent-seed tests, lesson interpretability review.

**Failure modes.** Multi-cell shapes blur whether the transformed unit is “each gray cell,” “each gray object,” or “each marker shape.” They also collapse multiple canonical objects into one connected component under generic gates.

**Limitations.** The selected rule is mathematically valid on connected 5-regions, but this curriculum chooses fidelity and identifiability over maximal domain breadth.

## 4. Seed count

**Choice.** Ordinary draws use three or four seeds. The exact diagnostic override allows one through four.

**Original rationale.** The baseline chose a count scaling with area, but its realized median was one object. The reason for prioritizing area scaling over canonical counts is not recorded.

**Alternatives considered.** Exactly three; exactly four; one through eight; area-proportional counts.

**Probes.** Canonical count distribution (`3` and `4`), distribution gate baseline (`1.0` versus `3.5`), strict override matrix, self-check census.

**Failure modes.** Too few seeds underteach union and independent local action. Too many seeds flood the output and obscure individual halos.

**Limitations.** The explicit one-seed override triggers a generic minimal-impostor warning. It is retained as a lawful diagnostic axis and is absent from ordinary training draws.

## 5. Grid dimensions and canonical mass

**Choice.** Use a deterministic difficulty/profile schedule over `7..15`, with two 9×9 profiles in every four-example cycle.

**Original rationale.** The baseline varied easy 4..8, medium 8..16, and hard 14..24 to add scale diversity. No evidence justified the extreme mismatch, and the pinned census had zero canonical-profile support.

**Alternatives considered.** All 9×9; 25% 9×9 plus extrapolation; uniform 7..15; retain 4..24.

**Probes.** Strict canonical-profile floor, axis-span detector, distribution census, focused cycle tests.

**Failure modes.** All 9×9 leaves dimension overrides untapped and provides no scale generalization. Too little canonical mass fails the 25% profile threshold and can train a distribution unlike evaluation. Very large grids change density and visual attention demands.

**Limitations.** The exact dimension schedule is hand-designed from the selected rule and three public examples; it is not learned from a larger empirical task family.

## 6. Four-profile schedule

**Choice.** Cycle `canonical_anchor`, `off_lattice`, `edge_clip`, and `overlap` by `sample_index % 4`.

**Original rationale.** The baseline independently randomized layouts and shapes. That created variety but offered no guarantee that a training lesson contained decisive evidence.

**Alternatives considered.** Independent random profiles; weighted random profiles; six or eight profiles; canonical-only placement.

**Probes.** Every sliding four-demo window across three bands and multiple starting residues; 48-lesson task-local audit; semantic rival survival tests.

**Failure modes.** Independent randomness can omit the one counterexample needed to reject a shortcut. A longer schedule may exceed the trainer's demonstration budget.

**Limitations.** The schedule assumes four demonstrations are available. A one- or two-demo consumer cannot receive the same identifiability guarantee.

## 7. Canonical anchor placement

**Choice.** Place seeds at generalized macrocell centers `(row % 3 == 1, col % 3 == 1)`, with nonoverlapping halos.

**Original rationale.** This reproduces the visible canonical construction and supplies a familiar anchor.

**Alternatives considered.** Copy exact public masks; use arbitrary interior points; omit canonical-looking scenes.

**Probes.** Profile-isolation regression and exact-profile gate.

**Failure modes.** By itself, this profile is ambiguous with “fill the containing 3×3 macrocell.”

**Limitations.** It must always be paired with off-lattice evidence; `lesson_identifiable` enforces that at the four-demo level.

## 8. Off-lattice placement

**Choice.** Require at least one interior seed outside the macrocell-center lattice and keep all halos disjoint.

**Original rationale.** New. It directly targets the strongest wrong rule that fits every public pair.

**Alternatives considered.** Shift every seed; use only one off-lattice seed; allow edge/overlap confounds.

**Probes.** Named `aligned_macrocell` rival, witness claim, profile-isolation tests.

**Failure modes.** If an off-lattice profile also clips at an edge or overlaps, a model may attribute the output difference to the wrong feature.

**Limitations.** One counterexample falsifies the named rival but does not enumerate every conceivable coordinate shortcut.

## 9. Edge-clipping placement

**Choice.** Require at least one border seed and keep all seed pairs at Chebyshev distance at least three.

**Original rationale.** New. Canonical seeds are interior, so clipping behavior was absent from public evidence despite being explicit in the selected rule.

**Alternatives considered.** Corners only; side edges only; no boundary examples.

**Probes.** `ignore_edge_seeds` rival, edge witness, focused profile tests.

**Failure modes.** Dense border seeds can turn clipping into a border-fill pattern rather than a local operation.

**Limitations.** The current profile guarantees some border evidence, not equal corner/side frequency.

## 10. Overlap placement

**Choice.** Require one interior pair at Chebyshev distance exactly two; any additional seed stays at least three cells from all others.

**Original rationale.** New. The canonical examples have disjoint 3×3 blocks, so they do not demonstrate union/merge behavior.

**Alternatives considered.** Adjacent input seeds; several overlapping pairs; only disjoint halos.

**Probes.** `nonoverlap_only` rival, overlap witness, profile-isolation tests.

**Failure modes.** Adjacent input seeds would violate singleton-object grammar. Multiple overlapping clusters would make attribution harder.

**Limitations.** The profile demonstrates pairwise overlap, not all possible multiway unions.

## 11. Difficulty semantics

**Choice.** Difficulty changes dimension and seed-count mass, not the rule, palette, or object grammar.

**Original rationale.** The baseline mapped difficulty primarily to large dimension bands.

**Alternatives considered.** Make hard mode use connected shapes; increase seed density sharply; ignore difficulty entirely.

**Probes.** Per-band strict-profile, witness, and override checks.

**Failure modes.** Band-specific grammars can teach three related but different tasks and leave some semantic branch absent from a band.

**Limitations.** “Hard” here is a controlled visual-scale shift, not a measured model-error calibration.

## 12. Public override surface

**Choice.** Expose only `grid_h`, `grid_w`, and `n_seeds`; validate unknown keys and recover all exact values from output.

**Original rationale.** The baseline declared eight axes, several of which were aliases, constants, unparseable, or not honored.

**Alternatives considered.** Repair every old axis; mark unprobeable axes diagnostic; remove overrides entirely.

**Probes.** Strict checker over 16,020 draws, 178 cases, three bands, including unknown-key injection.

**Failure modes.** An axis that cannot be observed can appear to work while being ignored. Silent unknown keys make typo tests meaningless.

**Limitations.** Semantic profile selection is deliberately scheduled rather than user-overridable, preventing callers from accidentally creating an unidentifiable four-demo lesson.

## 13. Self-check strictness

**Choice.** Validate structure, dimensions, ARC integer cells, `{0,5}` palette, background/seed presence, one-to-four seeds, and no 8-neighboring seed pair.

**Original rationale.** The imported self-check only required some `5` and colors within `{0,5}`.

**Alternatives considered.** Require only canonical 9×9/3–4 scenes; allow arbitrary connected gray regions; validate outputs too.

**Probes.** Canonical acceptance plus destructive mutation battery and task-local malformed-grid regressions.

**Failure modes.** An overly broad predicate lets corrupted training examples pass; an overly narrow one rejects lawful controlled extrapolation.

**Limitations.** Duplicate-row mutations can occasionally remain lawful by coincidence, so mutation rejection is high but not 100%.

## 14. Named semantic rivals

**Choice.** Model five concrete wrong rules and require every lesson to falsify each.

**Original rationale.** New. The baseline had no semantic contract.

**Alternatives considered.** Rely only on morphology gates; use an unrestricted program synthesizer; test one macrocell shortcut only.

**Probes.** Canonical ambiguity checks, witness/rival unit tests, every sliding four-demo window.

**Failure modes.** Named rivals are only as complete as reviewer imagination. A different shortcut can survive.

**Limitations.** The contract gives strong evidence against known high-probability shortcuts, not a proof of unique identification among all programs.

## 15. Task-local Racket-free auditor

**Choice.** Retain a small standard-library script under `workspace/`.

**Original rationale.** New, prompted by the host's missing Racket runtime and the need for reproducible partial evidence.

**Alternatives considered.** Rely only on pytest; vendor a Racket runtime; fake the Racket bridge.

**Probes.** 180 default draws and 48 sliding lessons.

**Failure modes.** The auditor can agree with a wrong Python mirror.

**Limitations.** It is explicitly supplemental and must never be presented as canonical execution evidence.
