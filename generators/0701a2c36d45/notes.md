# Working notes: 0701a2c36d45

## Review repair: review-9d6fe7cd15d4889b

The imported version 2.1.0 generator produced lawful labels but exposed a misleading public contract and weak teaching distribution. It had no canonical `RULE_HASH`, advertised an inert singleton `n_panels` control and degenerate textures, silently accepted unknown controls, rejected lawful cross-band overrides, and supplied no executable semantic lesson contract. The retained before battery therefore ended with 7 green stages, 2 advisory stages, and 3 failures.

Version 3.0.0 narrows the public surface to four pixel-recoverable axes:

- `panel_h`: 3..8
- `panel_w`: 3..8
- `shape_size`: 2..8
- `texture`: `plain`, `noise_robust`, `two_agree`, or `mixed_vote`

Every Cartesian combination is constructive in every difficulty band, including the 3×3 / size-8 boundary. Unknown keys, wrong types, and out-of-range values fail closed. `self_check` now validates panel grammar, rotations, colors, connectivity, and the realized vote-count pattern. The selected canonical Racket rule is unchanged and pinned by `RULE_HASH = "606946fe96ab"`.

The decisive teaching repair is the six-step schedule:

`mixed_vote, plain, mixed_vote, noise_robust, mixed_vote, two_agree`

A mixed-vote item contains both a one-vote distractor and a two-vote signal. At least two such items occur in every five consecutive samples, so holding out any one pair still leaves direct evidence against union, unanimity, and first-panel shortcuts; adaptive header codes separately refute ignoring rotations. The source-bound 300-lesson census materialized 1,500 unique inputs and found zero production or held-out-query ambiguities against the four declared rivals. The task-local cyclic probe exhausts all six starts in all three bands (18 windows, 90 rotations) with zero survivors and zero hook failures.

Regression tests live under `tests/test_generator.py`. Independent returned-pixel analysis and the exhaustive cyclic authoring tool live under `workspace/`; neither replaces the Racket-labelled census.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `21684db161734b5f174a398518e313bb0ed76198b4ace6be25ccaabcce256589`.

# Decisions: 0701a2c36d45

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical and selected `target_code` unchanged and pin it with `RULE_HASH = "606946fe96ab"`.

**Rationale.** All canonical pairs were already solved, the rule-smoke stage was healthy, and the failures were in generator contract and teaching distribution. Changing authority would have conflated a data-quality repair with a task-definition change.

**Alternatives rejected.** Rewriting or simplifying the archival `raw_code`; replacing the rule with a Python mirror; narrowing the rule to the generated grammar. The archival source is text-divergent but execution-equivalent on canonical pairs and is not selected authority.

**Probe / failure mode.** Authority sync and 120-seed rule smoke are retained under `checks/after/checks/`. A future canonical rule edit would stale the declared hash and the solve binding.

## D2 — Remove misleading controls instead of preserving compatibility aliases

**Choice.** Expose only `panel_h`, `panel_w`, `shape_size`, and `texture`.

**Rationale.** Each is recoverable from returned pixels and has a lawful, testable effect. The old singleton `n_panels`, inert shape aliases, and negative/degenerate textures made the API look richer while reducing training quality.

**Alternatives rejected.** Keeping old names as silent aliases; advertising negative fixtures as normal data; declaring large incompatibility tables. Silent aliases would remain unobservable, and negative fixtures belong in tests rather than the positive sampler.

**Probe / failure mode.** The final 222-case override matrix accepted 19,980/19,980 attempts with exact recovery and rejected an unknown key. The public API is intentionally breaking for invalid old controls; callers must migrate rather than receive silently different data.

## D3 — Make every exact value legal in every difficulty band

**Choice.** Difficulty changes default weights, not the admissible exact domain. All bands accept dimensions 3..8 and size 2..8.

**Rationale.** A global exact override must not fail because a band’s random prior would not normally choose it. This eliminates the baseline cross-band rejection defect and keeps the Cartesian contract simple.

**Alternatives rejected.** Band-local override bounds or a long `INCOMPATIBLE_OVERRIDE_COMBINATIONS` list. Both would make advertised exact controls harder to reason about and test.

**Probe / failure mode.** Boundary tests include 3×3 / size 8 for both `two_agree` and `mixed_vote`, plus tall and wide cases in every band. The sampler is bounded at size 8 even on larger panels; denser motifs are outside this reviewed domain.

## D4 — Weight canonical dimensions without collapsing diversity

**Choice.** Heavily weight 4×4 panels in every band while retaining all dimensions 3..8 and difficulty-specific tail ordering.

**Rationale.** The canonical input profile is 16×4 with six colors. The baseline hard sample had zero support; final profile-floor evidence gives exact support in every band while still producing noncanonical sizes.

**Alternatives rejected.** Force every draw to 4×4; leave canonical support to chance; create a separate canonical-only difficulty. Fixed dimensions would erase useful geometry variation, while accidental support already failed.

**Probe / failure mode.** Final exact hits were 14/20 easy, 15/20 medium, and 16/20 hard. This weighting is intentionally stronger than natural prevalence and should be revisited if downstream sampling already balances canonical profiles.

## D5 — Use connected asymmetric motifs with constructive fallbacks

**Choice.** Grow a connected motif inside the square supported by all quarter-turns, require asymmetry when possible, and retain explicit connected fallback shapes for sizes 2..8.

**Rationale.** Connectivity matches the task’s object interpretation. Asymmetry makes header rotations observable. Explicit fallbacks make boundary overrides deterministic rather than probabilistically flaky.

**Alternatives rejected.** Arbitrary independent pixels, only one fixed motif per size, or retry-until-success without a fallback. Independent pixels weaken object structure; fixed motifs reduce diversity; unbounded retries create hidden generation failures.

**Probe / failure mode.** `self_check` verifies connected monochrome panels and legal normalized rotations. The domain excludes disconnected motifs and bases larger than eight cells.

## D6 — Represent majority semantics with four named textures

**Choice.** Keep `plain`, add `noise_robust`, `two_agree`, and `mixed_vote` with exact vote-count definitions.

**Rationale.** Full agreement alone cannot distinguish majority from union, unanimity, or copying one panel. One-vote and two-vote cells teach opposite sides of the threshold. `mixed_vote` places both distinctions in a single lawful example.

**Alternatives rejected.** Add arbitrary panel corruption; use malformed “negative” examples; rely on separate lessons containing exactly one noise and one signal item. Arbitrary corruption is hard to validate, malformed examples are outside the rule domain, and singleton witnesses disappear under query rotation.

**Probe / failure mode.** Independent `review_probe.vote_profile` checks realized counts and outputs. Canonical examples with richer pairwise overlaps are classified separately as lawful `canonical_overlap`, not forced into the simplified generated texture taxonomy.

## D7 — Six-step schedule with repeated mixed-vote evidence

**Choice.** Use `mixed, plain, mixed, noise, mixed, two_agree`, four demonstrations, and one query from consecutive samples.

**Rationale.** At least two mixed examples occur in every five-item window, so removing any one pair leaves a mixed example among the demonstrations. This directly supports arbitrary one-query rotations.

**Alternative that failed.** A four-slot schedule with one noise and one two-agree witness passed ordered lessons but failed 18/60 semantic-gate hold-outs: removing the sole noise left the union shortcut unrefuted; removing the sole two-agree item left unanimity unrefuted. That failure is retained in `checks/mixed-profile-tests-red.log` and intermediate semantic evidence.

**Probe / failure mode.** The final source-bound census found 0/1,500 ambiguous rotations. `workspace/cyclic_lesson_probe.py` additionally exhausts all six starts in all three bands. The deterministic rhythm is a curriculum choice, not evidence of universal induction.

## D8 — Choose header codes that visibly matter

**Choice.** Search lawful header-code triples and prefer one where the `ignore_header_rotations` rival disagrees with the majority output.

**Rationale.** Random codes can be semantically redundant for symmetric motifs. A header that is present but unnecessary does not teach contextual control.

**Alternatives rejected.** Fixed codes, unconstrained random codes, or excluding all symmetric motifs. Adaptive choice preserves motif diversity while ensuring the cue changes the prediction whenever possible.

**Probe / failure mode.** `rotation_required` fired and refuted its rival in all retained semantic witness checks. Some mathematical motifs can be rotation-invariant; the constructor’s asymmetric base and explicit fallback minimize that case.

## D9 — Fail closed in `self_check`

**Choice.** Validate rectangularity, exact chunk grammar, header domain, separators, equal panel sizes, reserved colors, distinct monochrome panels, connectivity, normalized fit, vote texture, base-size range, and nonempty majority output.

**Rationale.** The baseline validator accepted degenerate textures and could not establish override observability. Training data should be rejected before rule execution when its claimed semantics cannot be reconstructed.

**Alternatives rejected.** A structural-only validator or trusting generator internals. Both permit drift between advertised semantics and actual pixels.

**Probe / failure mode.** Mutation tests cover broken header/separator, empty panel, stray 9, and unsupported multi-noise patterns. Validation recognizes actual canonical pairwise-overlap examples so strictness does not reject authority-linked inputs.

## D10 — Independent probes and finite rival scope

**Choice.** Keep returned-pixel analysis in `workspace/review_probe.py`; add exhaustive deterministic scheduling in `workspace/cyclic_lesson_probe.py`; use the source-bound shared census for Racket labels.

**Rationale.** A production helper testing itself can make a defect invisible. The independent parser catches mismatches in panel segmentation, rotation normalization, vote counts, and observable controls. The cyclic tool makes deterministic residue coverage cheap.

**Alternatives rejected.** Copy production helper outputs into tests; claim the generic 12-lesson smoke test is exhaustive; claim finite rivals prove unique reasoning.

**Probe / failure mode.** Task tests and cyclic probes are mirror-labelled authoring evidence; the 300-lesson Racket census is the population check. Undeclared hypotheses remain unknown.

## D11 — Curriculum annotations

`contextual_gating` is marked present because header symbols determine per-panel rotation and `ignore_header_rotations` is an executable rival. `multi_rule_interaction` is marked present because panel rotation feeds a two-of-three vote, with union and unanimity distinguished by generated mixed evidence. `sequential_state` is not applicable: no evolving state is carried across steps. `task_defined_symbols` is left unknown rather than double-counting the same header cue without a separate symbol-learning analysis.

## D12 — Audit and solve boundaries

The two audit targets were reviewed read-only and have Racket-backed counterexamples under `checks/audit/`. The post-repair solve was prepared only after generator bytes were frozen; during it, the generator and reference rule remained closed. Earlier exposure is recorded as `yes`, and hidden-query accuracy is not claimed.
