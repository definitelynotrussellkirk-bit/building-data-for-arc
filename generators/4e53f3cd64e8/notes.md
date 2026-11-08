# Working notes: 4e53f3cd64e8

## Current rule and source identity

The intended rule is the canonical **legend-ordered component gallery** transformation:

1. Read every nonzero cell in row 0, from left to right, as an ordered color legend. Zeros may separate legend entries.
2. Treat row 1 as a blank separator.
3. In the body, find exactly one homogeneous 4-connected component for each legend color.
4. Crop each component to its bounding box and pack the crops left-to-right in legend order, top-aligned, with one blank column between crops.

Generator version: `2.0.0`. Final generator SHA-256: `1037a8625fb543c21cf04d37f41eca4a9d270a970b852e11c172f0d02240be5f`. Canonical authority is pinned by `RULE_HASH = "5bdc8d1d0941"`. The Racket authority and canonical examples were not changed.

## Prior evidence used as a lead

I used retained return `review-e0dbd5b3721b1ec3:v0001`, recorded in `evidence/review_index.json`, as the specific lead. It was bound to baseline source SHA-256 `f1017aa1d21f178eeb8c9eee69d6fb8ef66f52ab31f0f6e6b60377b775d06ee4` and reported that `texture="missing_legend_blob"` admitted a legend color with no body component, `n_legend` was ignored, unknown controls were swallowed, authority was unpinned, and no task-local tests existed.

## Reversed and retained decisions

- **Reversed:** the old invariant treated the legend as a contiguous nonzero prefix. Canonical examples contain zeros before later legend entries, and the authority reads all nonzero top-row cells. The new parser and validator therefore read all nonzero row-0 cells in order.
- **Reversed:** the old nine-axis metadata advertised controls that generation did not consume. The public contract is now only four exact, pixel-observable axes: `grid_h`, `grid_w`, `n_legend`, and `palette_kind`.
- **Reversed:** degenerate textures were callable through production overrides. Retired and unknown axes are now rejected rather than silently creating malformed training inputs.
- **Retained:** row 1 is a separator and the body contains isolated colored objects. The stronger contract now requires exactly one component for every legend color and no unlisted body colors.
- **Retained:** output order is supplied by the legend, not by body location or numeric color rank.

## Construction and validation

The generator uses a constructive layout: 3–4 distinct legend colors, separated legend positions, one 3–5-cell connected component per color, and six mutually isolated 3x3 body slots. Component-to-slot assignment is shuffled independently of legend order. Legend order is forced away from numeric order, and every generated legend has a gap, so two plausible shortcuts are exposed on every draw.

`self_check` now validates rectangular ARC colors, dimensions, legend cardinality and uniqueness, the blank separator, component homogeneity, allowed colors, component size/bounds, and exactly one component per legend color. `strict_canonical_like` is the same lawful manifold. `observe_overrides` recovers all four advertised controls from pixels. Scalar call validation rejects booleans/coercions, negative indices, unknown difficulties, unknown axes, retired textures, and out-of-domain values.

A Python authority mirror is included for focused tests and rival definitions. It matches all five canonical input/output pairs. It is not a replacement for the pinned Racket authority.

## Teaching contract

Two executable witness/rival pairs are declared:

- `read_all_nonzero_legend_cells` refutes `contiguous_prefix_only`.
- `preserve_legend_order` refutes `numeric_color_order`.

`EXAMPLES_NEEDED = 2`, `MIN_STRICT_FRAC = 1.0`, and `lesson_identifiable` rejects a lesson when a declared rival fits all demonstrations but changes the query. The retained fixture `counterexamples/legend-gaps-and-order.json` exercises both rivals. `counterexamples/missing-legend-component.json` freezes the prior validator defect.

## Verification summary

Against final source SHA-256 `1037a8625fb543c21cf04d37f41eca4a9d270a970b852e11c172f0d02240be5f`:

- The strict after battery is 12/12 green; before repair it was 6 green, one advisory, and five failed stages.
- Portable task tests are 49/49 passing.
- Exact profile support is 18/60 overall: easy 5/20, medium 9/20, hard 4/20; envelope support is 60/60 and all five canonical inputs pass validation.
- Override audit accepted 9,000/9,000 planned calls with zero findings or warnings and rejected the unknown-key probe.
- Semantic census produced 600/600 strict inputs; both declared witnesses fired and both rivals were refuted throughout the checked support.
- Extended lesson census materialized 300 lessons (100 per band), 900 unique labeled inputs, and 900 held-out query rotations with zero ambiguity, hook warnings, scoring errors, or rotation failures.
- The visible-only reviewer solve passed 3/3 displayed examples in one revision. Earlier rule exposure is recorded as `yes`; reference consultation during the solve is recorded as `no`.

Evidence is under `checks/after/`, `checks/task-tests/`, `checks/lesson-census.json`, and `solve/`.

## Known limits and open findings

- The semantic evidence covers two declared task-specific rivals plus bounded generic mutations; it is not a proof of unique induction against every possible hypothesis.
- The component shape library, four exact palette families, and six coarse placement slots are finite. Slot assignment and legend order are randomized, but a future expansion could jitter components within larger legal regions and broaden color-role support without weakening isolation.
- The profile anchor deliberately places one quarter of default sample indices on canonical `(height, width, distinct-color-count)` support. This satisfies support floors but is not an empirical estimate of a natural task distribution.
- Query rotation was exhaustively applied to each of the 300 materialized three-pair lessons, but the census does not enumerate every seed or every possible cyclic schedule start.
- Training approval remains outside this review; all reports explicitly leave `training_admitted` false.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e0dbd5b3721b1ec3:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `f1017aa1d21f178eeb8c9eee69d6fb8ef66f52ab31f0f6e6b60377b775d06ee4`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted reviewer-reported repair source1037a8625fb543c21cf04d37f41eca4a9d270a970b852e11c172f0d02240be5f requires one lawful body component for each legend color, exact observable controls, unknown-key rejection and pinned rule5bdc8d1d0941. Missing-legend-component regression retained;49 tests and9000 overrides reported clean. Resolves this old-source validator/control finding, not all possible semantic rivals or a new maintainer test claim.

### Assessment or prior finding

## 4e53f3cd64e8

**Reproduced defect — validator and exact-control contract.** Audited generator SHA-256: `f1017aa1d21f178eeb8c9eee69d6fb8ef66f52ab31f0f6e6b60377b775d06ee4`.

`generate(0, 0, texture="missing_legend_blob")` creates legend colors `[4, 6, 7]` but body blobs only for `[4, 6]`; color `7` is absent from the scene body even though the generator's own invariant requires at least one blob per legend color. `self_check` returns `[]`, so the malformed scene is admitted. The same source advertises `n_legend`, but `generate(seed, seed, n_legend=2)` returned 3 or 4 legend colors for all 16 tested seeds. It has no `observe_overrides`, no `RULE_HASH`, and no task-local tests.

Reproducer and exact grid: `checks/audit/4e53f3cd64e8/repro.py` and `checks/audit/4e53f3cd64e8/repro.json`. Official portable-test result: `checks/audit/4e53f3cd64e8-task-tests/result.json` (`test_status: no_tests`). Suggested repair: make legend count an exact consumed control, validate every legend/body correspondence, pin authority, and add a regression for the retained missing-color texture.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e0dbd5b3721b1ec3-v0001/audit_assets.json), manifest SHA-256 `2edea73b2ed7572d3610f9beeec577fb9c06e0527b46b5b5041d30d92826c701`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `1037a8625fb543c21cf04d37f41eca4a9d270a970b852e11c172f0d02240be5f`.

# Design and review decisions

All final measurements in this document bind to generator SHA-256 `1037a8625fb543c21cf04d37f41eca4a9d270a970b852e11c172f0d02240be5f` unless stated otherwise.

## D1 — Keep the canonical Racket authority unchanged

**Original rationale:** Unknown. The baseline generator was inconsistent, but `rule_smoke`, `racket_lint`, and `authority_sync` were green against the pinned canonical examples.

**Alternatives considered:** change the rule to match the contiguous-prefix generator; change canonical data; repair only labels downstream.

**Probe:** compared all five canonical pairs with the authority and a separately implemented Python mirror. Canonical inputs include legend colors after zeros, and authority output uses them.

**Decision:** repair the generator to the authority and pin `RULE_HASH = "5bdc8d1d0941"`. No Racket or canonical-data edit.

**Failure mode/limit:** the Python mirror is only test support. Authority remains the Racket source identified in battery and census reports.

## D2 — Read all nonzero top-row cells, not a contiguous prefix

**Original rationale:** Baseline source explicitly assumed a contiguous prefix, but no supporting evidence was recorded.

**Alternatives considered:** contiguous prefix; longest nonzero run; fixed legend columns.

**Probe:** canonical-pair inspection and the retained `counterexamples/legend-gaps-and-order.json` witness. The `contiguous_prefix_only` rival disagrees with the authority.

**Decision:** legend is `[value for value in row_0 if value != 0]` in left-to-right order.

**Failure mode/limit:** this assumes row 0 is the legend channel and row 1 is a separator, as in every canonical pair. Inputs outside that documented manifold are rejected.

## D3 — Require exactly one body component per legend color

**Original rationale:** Baseline invariants said at least one blob per color, but `self_check` only required one matching body cell in total and explicitly admitted a missing-color degenerate.

**Alternatives considered:** permit missing slots; permit multiple same-color components and merge them; allow unlisted distractor colors.

**Probe:** `counterexamples/missing-legend-component.json` failed before the validator repair and is now rejected with a color-specific component-count error.

**Decision:** exactly one homogeneous 4-connected component for each legend color, no unlisted body colors, each component 3–5 cells and bounded by 3x3.

**Failure mode/limit:** canonical objects all fit this contract. Larger or disconnected same-color objects are intentionally outside generated support.

## D4 — Replace nine nominal axes with four honest exact axes

**Original rationale:** Baseline followed a generic metadata template (`palette_size`, `position_bias`, `n_distinct_colors`, `density`, `texture`) even though generation did not consume most of them.

**Alternatives considered:** implement every old axis; keep inert singleton diagnostics; retain degenerate textures as public controls.

**Probe:** baseline override battery failed with ignored values, narrowed difficulty ranges, unknown-key acceptance, and no observability. Task-local red tests first asserted exact round trips and rejection behavior.

**Decision:** expose only `grid_h`, `grid_w`, `n_legend`, and `palette_kind`; reject unknown and retired keys. All four round-trip through `observe_overrides` in every difficulty band.

**Failure mode/limit:** fewer knobs mean less nominal variety, but the remaining contract is truthful and directly testable. Degenerate cases survive only as retained fixtures, not production samples.

## D5 — Make palette kind observable from pixels

**Original rationale:** Unknown; baseline `palette_kind` and `texture` were metadata aliases but did not determine the palette.

**Alternatives considered:** record hidden provenance only; infer kind from RNG state; permit overlapping palette families.

**Probe:** exact override tests compare requested controls with `observe_overrides(grid)` and the 9,000-case override matrix.

**Decision:** use disjoint exact color sets for each `(palette_kind, n_legend)` and shuffle only order. This makes kind recoverable from the returned color set.

**Failure mode/limit:** four finite palettes can become a style cue. They control data coverage, not the transformation rule; broader role-preserving palettes are a future extension.

## D6 — Use constructive isolated slots instead of random blob retries

**Original rationale:** Baseline used `grow_blob` with a shared occupied set; a failed growth attempt could silently omit a required color.

**Alternatives considered:** increase retry counts; generate then reject/resample; place arbitrary coordinates with pairwise-distance checks.

**Probe:** constructive outputs were validated over 600 semantic-gate draws, 9,000 override draws, 900 lesson inputs, and focused deterministic sampling without a construction failure.

**Decision:** choose among six guttered 3x3 slots and finite connected templates. Components cannot merge or leave the grid by construction.

**Failure mode/limit:** coarse slot support is visually narrower than arbitrary placement. Component assignment is shuffled to prevent slot order from encoding legend order, but future jitter would improve visual breadth.

## D7 — Force both core teaching witnesses on every generated input

**Original rationale:** Baseline had no semantic contract. A correct label alone did not establish that demonstrations teach gap-reading or sequence preservation.

**Alternatives considered:** rely on occasional random witnesses; use three or more demonstrations; check only canonical pairs.

**Probe:** generated legends always contain a gap and are forced away from numeric order. `contiguous_prefix_only` and `numeric_color_order` differ from the authority on all checked generated inputs.

**Decision:** declare executable witnesses/rivals and `lesson_identifiable`; use two demonstrations plus one query (`EXAMPLES_NEEDED = 2`).

**Failure mode/limit:** only two task-specific rivals are declared. The finite gate does not prove unique induction against every plausible program.

## D8 — Add deterministic canonical-profile anchors

**Original rationale:** Baseline dimensions and distinct-color support missed strict profile floors in at least one band.

**Alternatives considered:** sample exclusively from the five canonical profiles; broaden all draws uniformly and hope for hits; waive the profile gate.

**Probe:** final profile audit: easy 5/20, medium 9/20, hard 4/20 exact hits; 18/60 pooled and 60/60 envelope.

**Decision:** every fourth default sample index deterministically selects one canonical `(height, width, legend-count)` profile, with band offsets; other draws retain the full declared ranges and explicit overrides always win.

**Failure mode/limit:** the 25% anchor is an engineering support policy, not a claim about natural frequency. It creates periodic structure in `sample_index`, documented here and in code.

## D9 — Keep difficulty focused on crop complexity, not control validity

**Original rationale:** Baseline narrowed dimension bounds by difficulty, causing globally advertised exact values to fail in some bands.

**Alternatives considered:** publish band-specific valid domains; clamp exact overrides; retain narrow per-band dimensions.

**Probe:** parameterized tests apply low, high, and interior exact controls under `None`, easy, medium, and hard. The override matrix covers all three named bands.

**Decision:** all exact control domains are valid in every band. Difficulty changes the distribution of component sizes only.

**Failure mode/limit:** difficulty separation is modest and not a calibrated human difficulty measure.

## D10 — Require query rotations in the extended lesson census

**Original rationale:** Production lesson order alone can hide a rival that fails only when another pair becomes the query.

**Alternatives considered:** smoke-test the fixed query only; diagnostic rotations that cannot fail; enumerate a declared schedule period (none is declared).

**Probe:** `lesson-census --per-band 100 --rotate-query` materialized 300 lessons and held out every one of their 900 labeled pairs once.

**Decision:** report both production and required rotation verdicts. Both have zero ambiguity, hook warnings, and scoring errors against the declared rivals.

**Failure mode/limit:** rotations reuse 300 sampled bundles; they do not enumerate all seeds, semantic-equivalent inputs, or undeclared rivals.

## D11 — Record the visible solve as exposed but reference-free

**Original rationale:** Generator work necessarily exposed the rule before the solve episode; claiming blindness would be false.

**Alternatives considered:** skip the solve; mark exposure unknown; consult the reference during the solve.

**Probe:** the one submitted solution passed all three displayed examples. The solve tracker binds it to the final generator bytes.

**Decision:** finish with earlier exposure `yes`, reference consulted during solve `no`, and masked query label `unknown`.

**Failure mode/limit:** this is evidence that the displayed lesson is executable and coherent, not an independent blind-model evaluation.
