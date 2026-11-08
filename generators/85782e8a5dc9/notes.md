# Working notes: 85782e8a5dc9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1daf5109308eabf268f18745a624fbe518bf2641216d2b76199bd3dfe8dbbfd9`.

# Decisions: 85782e8a5dc9

The imported working notes did not preserve a rationale for the baseline's eight-axis design, and `evidence/associated_notes.jsonl` was empty. Decisions below therefore distinguish the measured baseline behavior from the repair rationale rather than attributing unsupported intent to the original author.

## D1 — Use the exact canonical 6×20 framed grammar

**Decision.** Generate exactly three 6×6 color-5 frames with 4×4 interiors, separated by blank columns 6 and 13. Require A:B to identify one supported non-identity transform and require the answer to be that transform applied to a distinct C motif.

**Why.** All five canonical inputs use 6×20 dimensions and one of three palette signatures. The baseline's variable 5×17/6×20/7×23-style geometry produced only 1/60 exact canonical-profile samples and zero easy/hard support. Fixing the grammar raises linked support without changing the mathematical rule.

**Rejected alternatives.** Merely loosen the profile threshold, or keep broad dimensions while oversampling 6×20. Both retain unnecessary off-profile mass and make exact controls harder to validate. A broader grammar can be added later only with canonical or explicit authority-backed evidence.

**Probe and failure mode.** `strict_canonical_like`, the profile-floor gate, and `test_default_distribution_stays_on_exact_canonical_shape_palette_profiles` enforce the boundary. The intentional limitation is no training coverage for other panel sizes.

## D2 — Replace eight misleading axes with one observable semantic axis

**Decision.** Expose only `scene_profile` with four exact values: `quarter_turn`, `half_turn_color_key`, `axis_reflection`, and `diagonal_reflection`. Reject unknown keys, invalid values, and invalid difficulty names.

**Why.** The baseline advertised eight axes, but two were single-token metadata, four helpful textures were byte-dead, negative fixtures appeared in the ordinary texture domain, and multiple numeric controls did not have reliable realized-value provenance. A smaller exact API is more useful to lesson builders than a large nominal one.

**Rejected alternatives.** Preserve legacy names as aliases, or mark dead axes diagnostic. Aliases perpetuate typo/fallback risk; diagnostic labels would add no data value. The baseline copy is retained at `workspace/generator.before.py` for comparison without keeping the broken public contract.

**Probe and failure mode.** `observe_overrides` recovers the profile from pixels. The final override matrix accepted 450/450 draws with zero findings. Future axes should be added only with an exact observer and cross-band tests.

## D3 — Cover the six transforms executed by the selected authority

**Decision.** Generate `rot90`, `rot180`, `flip_lr`, `flip_ud`, `transpose`, and `anti_transpose`. Map them to four human-readable profiles, allowing the axis and diagonal profiles to choose one of two paired transforms deterministically.

**Why.** This covers every ordinary non-identity branch supported by the selected rule while keeping the override vocabulary compact. The profile tells a lesson builder the semantic family; seed, sample index, and band choose the paired orientation without hiding a different rule.

**Rejected alternatives.** Add identity or a quarter-turn inverse as new ordinary branches. Identity weakens transfer evidence, while an unverified branch would change the reviewed task domain. Both can be reconsidered only with authority and canonical evidence.

**Probe and failure mode.** The task tests require all six transforms to appear. The final local audit observed all six, with counts retained in `checks/curriculum-audit.json`.

## D4 — Use fixed asymmetric supports and a color-keyed half-turn witness

**Decision.** Construct A and C from fixed five-cell supports in distinct D4 orbits, then vary orientation and colors. For the half-turn profile, use an occupancy support invariant under 180° while arranging colors so A and B differ.

**Why.** Fixed asymmetric supports guarantee unique transform inference, guarantee that T(C) differs from A/B/C, and remove rejection-loop tail risk. The half-turn support specifically refutes a canonical-fitting shortcut that infers transforms from occupancy alone.

**Rejected alternatives.** Continue random sparse motifs with up to 240 rejection attempts, or rely on naturally occurring multicolor symmetries. Rejection sampling is harder to audit and can introduce seed-dependent fallbacks; incidental witnesses do not guarantee lesson identifiability.

**Probe and failure mode.** `test_half_turn_profile_forces_color_aware_transform_inference` verifies equal masks, unequal colored motifs, and an occupancy-only wrong answer. This support is intentionally synthetic and may not represent every visual style a broader generator could offer.

## D5 — Let difficulty change palette richness, not the law

**Decision.** Easy uses one motif color except that the color-keyed half-turn requires at least two; medium uses two; hard uses three. Difficulty also participates in choosing the paired reflection variant, while an explicit `scene_profile` remains exact.

**Why.** This gives visible cross-band variation while preserving one rule and the same canonical shape. Every selected color is realized in C, so palette richness is observable rather than latent metadata.

**Rejected alternatives.** Make difficulty alter panel size, motif density, or lesson law. Those changes recreate profile drift or make lessons across bands semantically inconsistent.

**Probe and failure mode.** The final signatures are exactly `(6,20,3)`, `(6,20,4)`, and `(6,20,5)`. Easy one-color examples alone would not refute color-collapse, so the schedule's half-turn witness is forced to at least two colors.

## D6 — Require four demonstrations and declare executable rivals

**Decision.** Set `EXAMPLES_NEEDED = 4`; declare six callables in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`; declare the occupancy-only callable in `CANONICAL_SHORTCUTS`; and make `lesson_identifiable` validate labels and require direct rival falsification.

**Why.** Correct per-example labels do not guarantee useful training episodes. The canonical ledger itself does not refute occupancy-only inference, so the contract must test lesson-level evidence rather than count witnesses in isolation.

**Rejected alternatives.** Use prose-only rival names, a generic “wrong transform” placeholder, or two inference guesses. Non-executable claims cannot be gated; two guesses do not ensure that the demonstrations teach the intended rule.

**Probe and failure mode.** The semantic gate verified 6/6 rival claims and 12/12 sampled lessons. The finite rival list remains a lower bound on ambiguity, not a universal proof.

## D7 — Use a ten-step schedule with redundant critical witnesses

**Decision.** Use the cyclic sequence:

`quarter, half, quarter, half, axis, quarter, half, quarter, half, diagonal`.

Every five consecutive pairs contain at least two quarter-turn and two color-keyed half-turn examples. Therefore, after any one pair becomes the query, all four demonstrations retain at least one of each critical witness.

**Why.** The first repaired schedule used each semantic profile less redundantly. Ordinary fixed-query lessons passed, but rotating the query produced 450 ambiguous episodes out of 1,500. The failure was structural: the sole half-turn witness could become the query, allowing occupancy-only inference and color collapse to survive the remaining demonstrations.

**Rejected alternatives.** Disallow query rotation in the probe, resample only failing windows, or increase lesson size. The downstream policy may rotate labelled pairs, resampling hides deterministic holes, and a larger lesson costs more context. Redundancy fixes the actual four-demo contract.

**Probe and failure mode.** The RED evidence is `checks/query-rotation-red.log` and `checks/lesson-census-v3.0-ambiguous.json`; GREEN evidence is `checks/query-rotation-green.log`, `checks/lesson-census.json`, and `checks/curriculum-audit.json`. The schedule is intentionally nonuniform: reflections occur less often than critical disambiguators.

## D8 — Keep all generated examples lawful; do not emit negative fixtures as normal data

**Decision.** Remove `no_panels`, `identity_transform`, and `mismatched_transform` from the generator domain. Malformed grids are exercised in tests and rejected by `self_check` rather than labelled through the ordinary sampler.

**Why.** The baseline advertised these negative fixtures as valid textures even though they violated its own grammar. Mixing invalid negatives into a training generator creates undefined labels and contaminates override testing.

**Rejected alternative.** Retain a “degenerate” axis. That would be justified only for lawful edge cases with well-defined authority outputs, not malformed or rule-ambiguous inputs.

## D9 — Preserve the Racket authority and pin it

**Decision.** Add `RULE_HASH = "8de2ee81f8fa"` and do not edit the canonical row or selected Racket source.

**Why.** Rule smoke and authority sync already showed the authority was coherent; defects were in sampling and teaching. Changing both authority and generator would expand the review surface without evidence of a rule bug.

**Probe and failure mode.** Final rule smoke, Racket lint, and authority sync are green. The authority-set SHA-256 remains `f6ef427971193323a71cfba6771ae861c0b52e21b87b6f01da09913c83a1ed84`.

## D10 — Retain a reusable declaration-driven curriculum audit

**Decision.** Add `workspace/curriculum_audit.py` and a task-local test. The tool imports the generator's actual rivals and shortcuts, checks all supplied starts and query rotations, records source SHA-256 and coverage, and fails loudly on exceptions or surviving rivals.

**Why.** It found and then guards the schedule defect that per-example gates could not see. Reading declarations directly prevents the audit's rival list from silently drifting away from the generator contract.

**Rejected alternative.** Keep a one-off notebook or copied name list. That would be difficult for future agents to replay and could falsely pass after declarations change.

## Distribution summary

- Shape: fixed 6×20 input, three 6×6 frames, three 4×4 interiors.
- Ordinary transforms: six non-identity D4 branches supported by the selected authority.
- Public control: four exact `scene_profile` values.
- Palette: one/two/three motif colors by band, with two minimum for the color-keyed half-turn.
- Lesson assembly: four demonstrations plus one query, cyclic ten-step schedule, query rotation permitted and tested.
- Invalid cases: rejected, never silently labelled as ordinary training examples.

## Remaining limitations

The final measurements cover the canonical ledger, the complete declared profile space, 300 Racket-backed production lessons, and 1,536 task-local deterministic lesson windows. They do not prove correctness outside the fixed 6×20 domain or identifiability against undeclared algorithms. The retained schedule assumes a downstream lesson contains five consecutive generated pairs and may rotate any one into the query role; a different assembler should rerun the declaration-driven audit under its own policy.


## D11 — Parametric transfer-count prototype (review-94fce2532ffa954b)

**Decision.** Keep the exact canonical `once` program as the default and add a
private `applications=twice` setting that infers the same input-dependent A→B
D4 transform and applies it twice to C. The adapter supports 2..6 demonstrations
and stable 1..4 query prefixes; the fourth query is an exact 30×30 stress case.

**Why this parameter.** It changes a single compositional step without changing
input parsing or the transform-inference problem. The setting alone cannot
predict the answer: the A/B panels must first yield the transform intermediate.
A protected-Racket counterfactual replacing the retained quarter-turn
intermediate with a half-turn changes eight output cells.

**Evidence and limits.** The task-local finite audit covered 768 episodes /
5,888 pairs across both settings and demo counts 2, 3, and 6. Native
qualification covered 136 protected-Racket evaluations, and four public
projections exclude settings, programs, and query answers. This is a
reviewer-ready prototype only: owner integration, fresh qualification,
acceptance replay, and any training-admission decision remain pending.
