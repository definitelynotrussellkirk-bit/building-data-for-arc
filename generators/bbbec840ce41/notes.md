# `bbbec840ce41` generator notes

## Intended rule

For an `n × n` grid, preserve every nonzero cell `(r, c)` and copy the same color to `(n - 1 - c, n - 1 - r)`, its reflection across the anti-diagonal. The reviewed authority is unchanged and pinned by `RULE_HASH = "655e255b5949"`.

## Current design: version 2.0.0

Generation constructs 4..12 colored source cells on or above the anti-diagonal of a 6..16 square. Every sample has at least one strict off-axis source, at least two colors, and a uniquely colored off-axis coordinate anchor with a non-8 color. This makes the transformation nonidentity and exposes axis, copy-vs-move, and color-preservation semantics.

The public exact controls are `grid_n`, `n_cells`, `n_colors`, and `n_axis`. `observe_overrides` recovers all four from pixels. Unknown controls fail; impossible count pairs (`n_colors > n_cells`, `n_axis >= n_cells`) raise `IncompatibleOverrides` with the conflicting axes.

Every 20-sample block reserves indices 0, 4, 8, 12, and 16 for the five canonical profiles. Other indices retain difficulty-weighted broad draws. The schedule guarantees exact canonical-profile support in easy, medium, and hard without making all samples canonical clones.

The semantic contract checks identity, main-diagonal, half-turn, move-not-copy, and fixed-mirror-color rivals. `lesson_identifiable` validates four-demo lessons and their query. `counterexamples/semantic_witness.json` refutes all five rivals; `counterexamples/identity_all_axis.json` retains the old identity failure.

## Reversed baseline decisions

Version 1.3.1 exposed constant/dead axes and placed `empty_grid`, `all_on_antidiag`, and `anti_symmetric` in the ordinary texture domain. It also had no rule pin, semantic contract, canonical-profile schedule, or probative validator. Those choices were removed because baseline lint/defect checks found dead controls and lawful-domain overlap, `self_check` rejected 0/57 destructive mutations, and the hard band had 0/20 exact canonical-profile hits. Evidence is retained under `checks/before/` and `checks/before-override/` in review `review-5e3868cd57b705df`.

## Verification

Final review evidence reports 12/12 battery stages green, 38/38 focused tests, 32,040 override attempts with zero findings, and 5/5 canonical inputs accepted. A 100-lesson-per-band census materialized 300 lessons and 1,500 five-way query rotations with zero ambiguity against the declared rivals.

## Assumptions and limits

The generator chooses the on/above-axis side as sources even though the authority itself is symmetric. This is an instructional orientation that keeps added copies visually separable; it is not a restriction on the reference rule. The semantic rival set is finite, so passing it does not prove unique induction against every possible program. No open blocking finding remains in the declared generator domain.
## Current reviewer considerations

Source SHA-256: `33ec3a6cd523fc37a16a282f83ca44f7c26d7f081cf5bf561f1394e63405ac72`.

# Decisions for `bbbec840ce41` version 2.0.0

## 1. Preserve the authority; repair the teaching distribution

**Decision.** Keep the canonical Racket rule unchanged and pin its current hash, `655e255b5949`.

**Reason.** All five canonical examples agree on a simple rule: preserve every colored source cell and copy its color across the anti-diagonal. The baseline rule-smoke check already passed. The failures were in generator contracts and lesson quality, not labels or authority semantics.

**Rejected alternative.** Rewriting the authority to match one of the old texture modes would have converted a data-quality defect into a rule change and invalidated canonical provenance.

## 2. Replace eight nominal axes with four exact observable controls

**Prior choice.** Version 1.3.1 advertised geometry/count axes plus constant or dead axes such as `position_bias`, `density`, and texture values that did not reliably change pixels. The original notes contained no rationale; the likely goal was broad configurability, but the measured result was a placebo API.

**New choice.** Expose only:

- `grid_n` in 6..16;
- `n_cells` in 4..12;
- `n_colors` in 2..7;
- `n_axis` in 0..3.

All four are exactly recoverable by `observe_overrides`. Unknown keys are errors. `n_colors > n_cells` and `n_axis >= n_cells` are declared joint incompatibilities with machine-readable axis names.

**Reason.** A training/control API should describe returned pixels, not hidden RNG branches. Exact counts also make the override matrix a meaningful regression test.

**Rejected alternatives.** Keeping a free-form `texture` enum was rejected because it mixed lawful curricula with identity/blank negatives. Keeping one-token diagnostic axes was rejected because no consumer can observe or probe them.

## 3. Construct a nonidentity teaching witness in every input

**Decision.** Place all sources on or strictly above the anti-diagonal, require at least one strict off-axis source, and reserve one uniquely colored off-axis coordinate whose color is not 8.

**Reason.** This makes four facts visible in every lesson: the anti-diagonal axis, an actual added copy, preservation rather than movement, and color transport rather than fixed-color painting. Constructing the witness is safer than generating arbitrary cells and repeatedly rejecting bad draws.

**Failure modes addressed.** Blank grids, all-axis identity examples, one-color examples, lower-triangle source/copy collisions, and examples where every coordinate/color cue is duplicated.

**Reusable probes.** `counterexamples/identity_all_axis.json` must be rejected; `counterexamples/semantic_witness.json` must match the independent oracle and disagree with all five declared rivals.

**Known limit.** The grammar selects a source side of the symmetric law. This is deliberate instructional orientation, not a claim that lower-triangle inputs are illegal for the authority.

## 4. Use a deterministic canonical-profile floor plus broad draws

**Decision.** In every 20-sample block, residues 0, 4, 8, 12, and 16 realize the five canonical `(height, width, palette-size)` profiles; all other residues use difficulty-weighted broad counts and sizes.

**Reason.** The baseline hard band had zero canonical-profile support in 20 draws. Deterministic anchors guarantee coverage in every band and are reproducible under seed changes, while 15/20 residues remain broad.

**Rejected alternatives.** Pure rejection sampling was rejected because profile coverage would remain probabilistic and make tests flaky. Making every sample canonical-like was rejected because it would collapse size/count diversity and overfit the five authorities.

## 5. Declare executable rivals instead of relying on labels alone

**Decision.** Add five plausible competitors: identity, main-diagonal copy, half-turn copy, move-not-copy, and fixed mirror color. Add three witnesses and a `lesson_identifiable` hook that verifies labelled outputs and rejects a competitor that fits all demonstrations but changes the query.

**Reason.** Correct labels are insufficient when every demonstration also supports a shortcut. The named rivals reflect the most local, likely confusions for this transformation and are cheap to evaluate.

**Rejected alternative.** Treating canonical parity or morphological similarity as proof of teachability was rejected. Those gates cannot detect a rival that agrees with the sampled labels.

**Known limit.** The set is finite. Passing it is evidence against specified confusions, not proof that a unique rule is logically forced among all programs.

## 6. Four demonstrations; production order plus complete five-way rotations

**Decision.** Keep `EXAMPLES_NEEDED = 4`. Production lessons use four consecutive demonstrations and the next pair as query. Validate all cyclic four-demo windows in focused tests and hold out every one of the five materialized pairs in the large census.

**Reason.** One constructed input already refutes all declared rivals, so four examples provide diversity without inflating lesson cost. Rotating the query detects accidental dependence on pair ordering.

**Measured result.** 300 production lessons and 1,500 query rotations across easy/medium/hard had zero declared-rival ambiguity.

## 7. Make validation broad enough for canonical inputs but strict enough to be probative

**Decision.** `self_check` validates only pixel-level teaching invariants and accepts grids beyond the generator's default numeric ranges; `strict_canonical_like` separately checks the canonical size/count/palette envelope.

**Reason.** Mixing structural lawfulness with a narrow sampling profile would reject valid canonical inputs or turn `self_check` into generator-output recognition. Separating them supports both robust validation and explicit distribution measurement.

## 8. Retain failures as executable evidence

**Decision.** Add source-bound tests and two JSON counterexamples rather than only documenting the defects in prose.

**Reason.** The selected-task tests are copied into a portable runtime by the task-test stage. This protects the exact contracts during future review and makes the original identity shortcut reproducible without recovering version 1.3.1.

# Native parametric review — 2026-10-25

## Preserved authority and selected family

The production generator remains byte-exact at
`33ec3a6cd523fc37a16a282f83ca44f7c26d7f081cf5bf561f1394e63405ac72`.
The `finish=copy_only` setting is the exact selected canonical program,
SHA-256 `0ae69a5ec165c081798648684b5afc8f6a0ad2d8cc7ab46e7090abbddb395b27`.
The alternative `finish=largest_after_copy` first performs the canonical
anti-diagonal copy and then recolors the unique largest monochromatic
8-connected component to color 4.

The sampler constructs a rank inversion: a source-side distractor is largest
before copying, while a smaller near-axis diagonal cluster joins its reflection
and becomes largest only in the copied intermediate. This makes the second stage
consume the first stage rather than merely accompany it.

## Retained evidence and limits

- Complete staged task suite: 74 passed.
- Bounded self-audit: 12 jobs, 154 protected-Racket evaluations, 16 isolated
  one-query public turns, and no harmful survivor among the declared finite rivals.
- Native qualification: both settings, seeds 0 and 17, 3 demonstrations and 4
  queries, 40 protected-Racket labels.
- The source-bound counterfactual ranks objects before copying and produces a
  different final output on the retained 30x30 witness.

The finite rival set and sampled seeds are evidence, not a proof of unique
induction or measured training gain. Owner exact-source integration, fresh
acceptance, and any training admission remain separate downstream decisions.
