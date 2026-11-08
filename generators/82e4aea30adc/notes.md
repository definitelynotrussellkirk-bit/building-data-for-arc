# Working notes: 82e4aea30adc

## Intended rule

On a zero background, each nonzero 4-connected component must be a monochrome
hollow rectangle. Fill its complete zero interior gray (5) when the interior area
is exactly one; otherwise fill it orange (7). Preserve borders and exterior
background. Canonical `RULE_HASH`: `3b12f4f95260`.

## Current selected generator

Version `3.1.0`; final source SHA-256
`8122e09d9a781d591b1249670b6f5d2cf506e22494b6e3351e93b86cbf0071cf`.
The Racket authority and canonical rows are unchanged.

Changes from 3.0.0:

- strict literal-integer validation for `seed` and nonnegative `sample_index`,
  plus declared-difficulty validation in `generate` and `schedule_profile`;
- every `multi_only` and `mixed` scene contains a lawful frame with an outer
  dimension above 5;
- `large_frame_count`, `large_frame_support`, and the explicit rival
  `ignore_frames_larger_than_5` were added to semantic diagnostics.

The retained `3×7` counterexample proves why this support matters:
`counterexamples/large-frame-size-cap.json`. Baseline source
`ce8429e27d78ca2524560ce446e7bbe366aadb227fec3fa2be1a2df690d34342`
accepted the input but never generated such dimensions. Prior retained return
`review-0e695f899d2c24c6-v0001` was used only as a lead; current claims were
remeasured against selected bytes.

## Evidence

- Final battery: 12/12 green — `checks/after-v2/`.
- Portable task tests: 50/50 pass — `checks/task-tests-v2/`.
- Ordered lessons: 18/18 clean, 72 unique pairs —
  `checks/lesson-census-final.json`.
- Rotation diagnostic: 71/72 clean; the sole ambiguity is the separate
  `choose_one_fill_from_frame_count` rival —
  `checks/lesson-census-final-rotations.json`.
- Large-frame support: 64/64 explicit scenes and 108/108 targeted held-out
  positions — `checks/repair/large-frame-support-census.json`.

## Parametric prototype

`workspace/parametric/` proposes episode-level
`gray_max_interior_area ∈ {1,2}`. Setting 1 is byte-identical canonical; setting
2 makes interiors of area two gray as well. The parameter is fixed per episode,
all labels/rivals are executed in Racket, and public queries are masked. This is
a prototype only; evidence is `checks/parametric/gallery/`.

## Known limits and open findings

Production lessons assume the declared order of three demonstrations and one
query. Arbitrary query rotation is diagnostic-only: one of 72 final rotations
remains ambiguous for a frame-count rival, though the repaired size-cap rival is
refuted in all rotations. Finite declared-rival checks are not proof of unique
induction. `single_only` deliberately remains `3×3`; larger dimensional support
is carried by `mixed` and `multi_only` scenes.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0e695f899d2c24c6:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ce8429e27d78ca2524560ce446e7bbe366aadb227fec3fa2be1a2df690d34342`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit repair-bound closure ofold ce8429e27d78ca2524560ce446e7bbe366aadb227fec3fa2be1a2df690d34342 againstnew8122e09d9a781d591b1249670b6f5d2cf506e22494b6e3351e93b86cbf0071cf. Ownerstaticinspection confirms _LARGE_MULTI_SHAPES includes3x7/7x3/4x6/6x4 andbothmulti_only/mixed alwaysincludeone;ignore_frames_larger_than_5 registeredwithlarge_frame_support. test_multi_only_profile_emits_large_frame_in_every_band andtest_mixed_profile_also_emits_large_frame_in_every_band plusretained3x7counterexample coveroriginalgap. Reviewer64supportdraws/27cycliclessons108holdouts refutesizecaprival and50portable/freshtests pass. Independentframecount rotationambiguity1/72remains documented;closingonlyoldsizecapfinding,notgenericapproval orownerRacketexecution.

### Assessment or prior finding

## 82e4aea30adc

**Finding: lawful large frames are accepted but never generated.** `self_check` accepts any hollow rectangle at least 3×3, yet `_MULTI_SHAPES` restricts ordinary frames to outer dimensions at most 5. Across 1,152 deterministic draws over all difficulty bands, observed frame sizes were only 3×3, 3×4, 3×5, 4×3, 4×4, 4×5, 5×3, and 5×4. A shortcut that applies the correct fill rule only when both outer dimensions are at most 5 fits all generated data.

**Reproducer.** A lawful 3×7 hollow frame in a 7×11 grid passes `self_check` with no findings. The true rule fills its five-cell interior orange (7), while the size-capped shortcut leaves it empty. None of the named semantic rivals models this support boundary. Add occasional 3×7/7×3 and larger lawful frames, or tighten the declared lawful domain if those sizes are intentionally excluded.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-0e695f899d2c24c6-v0001/audit_assets.json), manifest SHA-256 `40b58a0fb779e643e99eef3d942fc695d07d1e5727b2d901bcb2a07564930d86`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `8122e09d9a781d591b1249670b6f5d2cf506e22494b6e3351e93b86cbf0071cf`.

# Decisions: 82e4aea30adc

## D1 — Preserve the canonical authority

**Choice.** Keep the Racket rule and canonical rows byte-for-byte unchanged.

**Reason.** The authority correctly implements the intended conditional fill and
all canonical outputs. The observed failures were sampler/control-contract
problems, not rule defects. `RULE_HASH` remains `3b12f4f95260` and the final
authority-sync stage is green.

**Rejected alternative.** Narrowing the rule to frame sizes already generated
would encode the shortcut instead of repairing support.

## D2 — Treat the >5-dimension cutoff as the strongest sampler shortcut

**Prior choice.** The baseline generated only frame sizes whose outer dimensions
were at most 5, although `self_check` accepted larger hollow rectangles.

**New choice.** Add a lawful large frame to every `multi_only` scene and declare
`ignore_frames_larger_than_5` as a rival with an executable witness.

**Reason.** A `3×7` frame is accepted, the canonical Racket program fills its five
interior cells orange, and the rival leaves them zero. The rival fits all five
canonical labelled pairs, so it is stronger than a merely malformed-input
shortcut. Evidence: `counterexamples/large-frame-size-cap.json` and
`checks/repair/large-frame-racket-final.json`.

**Rejected alternatives.** A validator-only counterexample would not teach the
rule. Randomly emitting a large frame with low probability would leave many
lessons ambiguous. Expanding every branch was unnecessary: `single_only` is kept
at `3×3` to retain the canonical one-cell gray case.

## D3 — Put a large witness in `mixed` scenes too

**Prior repair iteration.** Only `multi_only` scenes contained a large frame.
Production-ordered lessons passed, but a full four-position rotation probe found
13 ambiguous rotations in 72 because the sole `multi_only` pair could be held
out.

**New choice.** Give `mixed` scenes one large multi-cell frame as well.

**Reason.** Every four-pair cyclic window now retains a large-frame demonstration
regardless of which pair is queried. The final targeted probe covers 108 held-out
positions with zero size-cap ambiguities. Evidence:
`checks/repair/large-frame-support-census.json`. The failed intermediate census is
retained at `checks/lesson-census-small.json`.

## D4 — Reject scalar coercion at the public boundary

**Choice.** Require literal integer `seed`; require nonnegative literal integer
`sample_index`; validate `difficulty` in both `generate` and `schedule_profile`.

**Reason.** The baseline defect-lint accepted booleans, floats, strings, and
negative indices in public controls. Coercible values can alias schedules and
make replay provenance unreliable. The final defect-lint stage is green, and
focused regressions exercise all rejected classes.

## D5 — Use an interior-area threshold as the parametric extension

**Choice.** Prototype one parameter,
`gray_max_interior_area ∈ {1,2}`, selected once per episode.

**Reason.** It changes the executed transformation while preserving hollow-frame
extraction, interior measurement, and conditional filling. Setting 1 is the exact
canonical program. Setting 2 is nearby and inferable from examples containing an
interior of area 2.

**Rejected alternatives.** Border-color changes are cosmetic role reskins.
Changing frame count, dimensions, or placement changes only input sampling.
Per-object threshold resampling would violate episode-level semantics.

**Evidence.** `workspace/parametric/prototype.py`, its README and focused tests;
`checks/parametric/gallery/report.json` records two complete Racket-labelled
episodes and exact source/runtime hashes.

## D6 — Keep production ordering; report arbitrary rotation honestly

**Choice.** Preserve `EXAMPLES_NEEDED=3` and the ordered
`single_only → mixed → multi_only` curriculum rather than redesigning it solely
for arbitrary hold-outs.

**Reason.** Final ordered production evidence is 18/18 clean. A diagnostic
72-rotation census leaves one ambiguity for
`choose_one_fill_from_frame_count`, while the repaired size-cap rival is refuted
in all 72 rotations. The downstream production assembly is ordered; rotations
are not a required policy in this packet.

**Rejected alternatives.** Increasing demonstrations to four or changing two of
three schedule residues to `mixed` would likely remove the remaining diagnostic
ambiguity, but would alter lesson length or branch balance beyond the concrete
assigned defect. The exact ambiguity is retained for a future curriculum-only
change: `checks/lesson-census-final-rotations.json`.

## D7 — Preserve failed and bounded evidence

The before battery, failed intermediate rotation census, and interrupted
large 100-per-band stress attempt were not rewritten as successes. The final
source is supported by the complete 12-stage battery, 50-test portable snapshot,
18-lesson production census, 72-rotation diagnostic census, and bounded 108-
rotation size-cap probe. Finite coverage is reported as finite coverage.

## D8 — Audit without modifying audited generators

The two adversarial targets were inspected against their assigned source hashes.
I built reusable reproducer scripts under `checks/audit/` but made no source edits:
`2da4094bc0e1` has a strict-scalar public-contract defect, and
`f7b828a70061` has a perfect rightmost bbox-tie shortcut. See `AUDIT.md`.
