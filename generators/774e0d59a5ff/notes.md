# Current notes: `774e0d59a5ff`

## Intended rule and authority

A full color-5 center row divides an odd-height grid into equal panels. Preserve the input and copy every nonzero top-panel cell to the vertically reflected row below the divider, preserving column and color. The canonical Racket authority is unchanged and pinned by `RULE_HASH = "73a966cdbca0"`.

## Reversed design decision

The prior `1.x` generator advertised broad/inert palette, color-count, position, density, and texture controls, admitted negative fixtures through the ordinary texture domain, accepted unknown/coercible inputs, and had no semantic-teaching contract. The retained audit `review-aaaca94facfaf522:v0001` identified inert palette controls; the independent before battery confirmed the wider contract failure.

Version `2.0.0` replaces that API with five exact, observable axes: `panel_h`, `grid_w`, `marks`, `n_colors`, and `motif_style`. The change is deliberate rather than backward-compatible: a smaller truthful contract is preferable to controls that silently do nothing or cannot realize their declared range. Evidence is in `checks/before/` and `checks/after/`; task-local portable regressions are in `tests/test_generator_774e0d59a5ff.py`.

## Distribution choices

- Lawful dimensions are 9/11 rows and 8..11 columns.
- The top contains exactly 4..8 marks in exactly 1..4 non-divider colors.
- `points` is orthogonally independent; `mixed` contains a forced adjacent pair.
- Construction reserves reflected top positions, guaranteeing a non-vertically-symmetric motif and therefore a visible distinction between reflection and same-order row copying.
- Ordinary draws retain every exact override value but weight canonical-like size/palette profiles enough to hit the fixed per-band profile floor.
- Negative cases (`no_divider`, `no_top_marks`, filled bottom) are not lawful training axes.

## Teaching contract

Three demonstrations are required. The declared witness is `vertical_order`; the named plausible rival is `copy_without_reflection`. `lesson_identifiable` checks authority-consistent labels and requires demonstrations to refute that rival. The final 100-per-band census found 0/300 ambiguous production lessons and 0/1,200 ambiguous query rotations.

## Assumptions and limits

Color 5 is a fixed structural divider, not an interchangeable motif color. The generator intentionally samples sparse points/adjacent-pair motifs rather than every possible topology. The semantic checks cover the declared rival plus generic measured label mutations; they do not prove unique induction against every possible rule. The census is finite and reuses each materialized lesson for rotations; it does not enumerate every seed.

## Open findings

No blocking finding remains on the selected source. The catalog remains unapproved/unverified for training pending maintainer intake; this review does not change approval state.
## Current reviewer considerations

Source SHA-256: `f46389028fbae69f134ecffeff0ed6ceeea3b6556524c751ea73065ff689fe67`.

# Decisions for `774e0d59a5ff`

## D1 — Keep the canonical Racket authority unchanged

- **Prior choice/rationale:** The baseline already generated grids for the canonical vertical-reflection rule; the original rationale beyond the source summary is unknown.
- **New choice:** Preserve the authority and pin its normalized hash as `RULE_HASH = "73a966cdbca0"`.
- **Why:** All five canonical labeled pairs agree with an independent Python mirror, and before/after authority-sync and rule-smoke checks pass. The failures were in sampling and contracts, not labeling.
- **Rejected alternative:** Rewrite the Racket rule to match a narrower Python generator. That would alter the task rather than repair its data distribution.
- **Failure mode/limit:** A hash pin catches authority drift but does not by itself prove semantic correctness.
- **Evidence:** R1/R3; `checks/after/checks/774e0d59a5ff_after_authority_sync.json` and `checks/after/checks/774e0d59a5ff_after_rule_smoke.json`.

## D2 — Replace, rather than cosmetically patch, the advertised axes

- **Prior choice/rationale:** The baseline advertised broad size/count controls plus `palette_size`, `n_distinct_colors`, `position_bias`, `density`, and helpful/degenerate textures. Some may have been intended as future controls, but no retained rationale showed why inert controls should remain public.
- **New choice:** Advertise only five pixel-observable exact controls: `panel_h=4..5`, `grid_w=8..11`, `marks=4..8`, `n_colors=1..4`, and `motif_style=points|mixed`.
- **Why:** These controls span the actual lawful task grammar and can be reconstructed from the returned grid by `observe_overrides()`.
- **Rejected alternatives:** Keep inert axes as diagnostics; or silently narrow their ranges. Both preserve a misleading API and make targeted lesson construction unreproducible.
- **Probe:** The override battery exhausts 132 axis/boundary combinations over three bands and 30 seeds per case.
- **Failure mode/limit:** `motif_style` intentionally distinguishes only isolated points from a motif containing an adjacent pair; it is not a general topology taxonomy.
- **Evidence:** R1; `checks/after/checks/774e0d59a5ff_after_override.log`.

## D3 — Fail closed on calls and lawful-domain validation

- **Prior choice/rationale:** The baseline inherited permissive scalar coercions and accepted unknown keys; why this was considered acceptable is unknown.
- **New choice:** Require genuine nonnegative integer `seed`/`sample_index`, genuine integer exact axes, known difficulty values, and no unknown overrides. `self_check` now validates the full divider/top/bottom/color/count/asymmetry grammar.
- **Why:** Booleans, floats, strings, and typoed axes otherwise create silent duplicate or unintended data.
- **Rejected alternative:** Let `gen_ctx` coerce values and rely on downstream lint. This delayed failures and allowed byte-identical supposedly distinct examples.
- **Failure mode/limit:** This is intentionally a breaking change for callers that depended on coercion; those calls were outside the documented contract.
- **Evidence:** R1/R2; task-local tests and `checks/after/checks/774e0d59a5ff_after_defect_lint.log`.

## D4 — Use constructive motifs and exclude negative fixtures from ordinary sampling

- **Prior choice/rationale:** The baseline exposed `no_divider`, `no_top_marks`, and `bottom_already_filled` as valid textures, apparently to aid diagnostics. No evidence justified treating them as lawful training inputs.
- **New choice:** Generate only valid sparse motifs. `points` uses an orthogonally independent parity class; `mixed` forces an adjacent pair. Both reserve reflected cells so the top panel cannot be vertically symmetric.
- **Why:** Constructive placement honors exact mark/style requests without rejection loops and guarantees a decisive vertical-order witness.
- **Rejected alternatives:** Retain negative fixtures in `AXES`; or generate arbitrary positions and reject symmetric draws. The former pollutes the lawful domain; the latter makes exact overrides and deterministic coverage harder to reason about.
- **Failure mode/limit:** The distribution does not attempt every possible connected shape; it targets rule-relevant variation with exact observability.
- **Evidence:** R2/R3; tests `test_every_exact_axis_round_trips_in_every_band` and `test_defaults_are_deterministic_lawful_diverse_and_semantically_useful`.

## D5 — Weight ordinary draws toward canonical envelopes without replaying canonical grids

- **Prior choice/rationale:** The old sampler used approximately canonical dimensions but still missed hard-band canonical profiles in the fixed 20-draw gate.
- **New choice:** Keep full support for both panel heights, all widths, all mark counts, and all color counts while adding keyed duplicate weights for common canonical-like values, with easy/hard mark/color emphasis.
- **Why:** This satisfies the per-band profile floor while preserving broader combinatorial support and deterministic replay.
- **Rejected alternatives:** Hard-code canonical examples or canonical profiles by sample index; or restrict hard entirely to one profile. Both would reduce diversity and risk leakage/memorization.
- **Failure mode/limit:** Weighted support is not a promise of uniformity. The gate demonstrates at least one canonical profile per band in its fixed sample, not every profile in every finite window.
- **Evidence:** R4; `checks/after/checks/774e0d59a5ff_after_profile_floor.json` and task-local profile test.

## D6 — Require a three-demo lesson to refute row-copying without reflection

- **Prior choice/rationale:** The baseline had no executable lesson contract, so its intended demonstration count and teaching policy were unknown.
- **New choice:** Declare `EXAMPLES_NEEDED = 3`, a `vertical_order` witness, and the plausible competitor `copy_without_reflection`. `lesson_identifiable()` verifies all labels and requires at least one demonstration that refutes that rival.
- **Why:** Correct per-grid labels are insufficient when demonstrations also fit an easy wrong transformation.
- **Rejected alternatives:** Rely only on `self_check`; or require all possible rivals. The first misses teaching ambiguity, while the second is not computable without a bounded hypothesis set.
- **Failure mode/limit:** Passing the declared rival and generic measured mutations does not establish universal identifiability.
- **Evidence:** R3; semantic gate and `checks/lesson-census.summary.json`.

## D7 — Support arbitrary query rotation for this task

- **Prior choice/rationale:** Unknown; the baseline had no lesson assembly contract.
- **New choice:** Make every generated pair itself carry the decisive vertical-order witness, so any held-out query leaves three demonstrations that still refute the named rival.
- **Why:** Downstream assembly may rotate labeled pairs. This task can support that safely at negligible distribution cost.
- **Rejected alternative:** Declare an ordered-only curriculum. That would be valid for some tasks, but unnecessary here and more fragile for reuse.
- **Probe:** 300 lessons × 4 held-out positions = 1,200 query rotations, with 0 ambiguities or hook warnings.
- **Failure mode/limit:** The census reuses each materialized bundle and is finite; it does not enumerate all seeds or undeclared rivals.
- **Evidence:** `checks/lesson-census.json`.
