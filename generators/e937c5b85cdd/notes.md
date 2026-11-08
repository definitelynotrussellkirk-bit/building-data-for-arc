# Working notes: e937c5b85cdd

## Review 2026-10-19 — assignment review-623ff21514220397

Final selected source: version 4.2.0, SHA-256 `a7ed8b0d8fb5985134246f0b7d928ee5060461a8b08cb7ff9a7c7372765599cf`; canonical rule hash remains `538497122a9d`. Prior return `review-10a65405aae36591` was used only as a lead.

### Current rule and distribution

For each non-background cross, find its unique longest arm. Clear the frame cell faced by that arm and paint the opposite frame cell with the cross color. Frame/background roles remain fixed at 6/7; legal generated crosses use collision-free projection lanes and unique longest arms. The selected Racket rule and canonical data are unchanged.

Ordinary lessons retain three ordered demonstrations and one query from the established `canonical_0, free, teaching_0, teaching_1` cycle. On final bytes, the 100-lessons-per-band census materialized 300/300 lessons and 1,200 unique labelled inputs: zero ambiguity in production and zero ambiguity across 1,200 query rotations against `six_cell_template_only`, `paint_nearer_axis_border`, and `length_three_paints_farther`. This is finite declared-rival evidence, not universal identifiability; exact overrides and fixed textures are outside the ordinary teaching guarantee.

### Current repair

Direct `generate()` calls now reject malformed call scalars before context creation: seed must be an exact integer, sample index an exact nonnegative integer, and difficulty one of `None/easy/medium/hard`. This closes boolean aliases, float/string coercions, negative indices, and silent invalid-band fallback. Twelve sampled valid calls retained byte-identical grid hashes, so the production distribution and deterministic valid draws were not intentionally changed.

Focused input-contract and parametric tests pass; the portable task stage reports 53 tests plus 79 subtests, and the strict final battery is 12/12 green. No selected-task blocker remains.

### Parametric proposal

`workspace/parametric/` contains an isolated episode-level `projection_polarity` prototype. `opposite` is the exact canonical default; `facing` paints the border endpoint faced by the unique longest arm. Both exact Racket programs produced complete three-demo/one-query episodes whose demonstrations distinguish the chosen setting. This is proposal evidence only; it does not alter `generate()`, `RULE_HASH`, or approval identity.

### Open limits

No learner-loss study was run, undeclared rivals may remain, and the binary prototype was checked on two deterministic episodes rather than every seed. The strongest retained canonical-fitting shortcut and exact Racket disagreement witness remain in `counterexamples/current-shortcut/`.

## Review 2026-10-04 — assignment review-10a65405aae36591

Selected baseline: version 4.1.0, SHA-256 `d53cfef28f2b8c5a75dff2b0909a74efba6d85413bd136e24b909e8a2b0c320e`.
Repaired generator: version 4.2.0, SHA-256 `25b0edefd8fe5333c0d4d9ac13be097dc2fc59123cf13b5e5c4505014f014b4e`.
Canonical rule hash remains `538497122a9d`.

### Teaching and empirical support

All six canonical occurrences (three distinct pairs) fit three rivals: process only six-cell templates, paint the nearer axial border, and use farther-border distance only for seven-cell crosses. The last rival escaped the first two-rival candidate, producing 25/300 production ambiguities and 141/1,200 rotated-query ambiguities on its retained Racket-labelled census.

The final schedule is `canonical_0, free, teaching_0, teaching_1`, selected by `(seed + sample_index) % 4`. Every ordinary teaching scene has two length-3 crosses with opposite nearer/farther relations. Every four consecutive ordinary draws therefore retain a demonstration refuting all three rivals after one query holdout. Three demonstrations are declared explicitly. Exact controls, fixed textures, rejection/resampling and disconnected-index policies need separate analysis.

The old morphology signature is preserved for fixture compatibility. `strict_canonical_like` additionally requires every painted side to be nearer, matching all observed canonical scenes. The full profile appears at least once per complete cycle; the statistical floor is 0.20. Final off-diagonal checks measured 50/200 easy, 55/200 medium, and 58/200 hard. Free scenes retain unconstrained geometry, length-2/length-3 support, and single-cross examples; exact overrides take precedence over schedule choices.

### Other local repairs

Unknown override keys, including unknown keys with `None`, now raise. Numeric axes require actual integers, not booleans, strings or truncated floats. Lawful diagnostic textures declare their incompatibility with other non-None exact controls. `self_check` handles malformed containers with diagnostics; the pure output helper accepts tuple rows without mutating input. Task tests use public portable canonical helpers, retaining the original coverage and frozen fixture.

Two bound base-solution active target-code strings were synchronized to exact canonical formatting. No non-whitespace rule content, archival raw-code field, or canonical ledger byte changed. Intake still needs the `racket` component for these authority files.

### Measured evidence and limits

Final source passed the 12-stage battery, 25 direct task tests plus 79 subtests, and the supported portable task stage. The portable stage reports 197 passing JUnit cases because it duplicates 14 methods plus 79 subtests through a legacy fixture mapping; distinct focused coverage is 104 cases. The override matrix made 23,220 calls, with 17,550 accepted, 5,670 declared incompatible texture requests, and zero unexpected findings.

The production census covered 100 lessons per band, 1,200 unique Racket-labelled inputs and 1,200 query rotations: zero ambiguities/errors for all three rivals. The direct cycle probe covered seeds 0–11, indices 0–6, all bands and four starts: 252 generated draws, 164 unique labelled inputs including an override control, 144 overlapping windows and 576 holdouts, also clean. These are finite declared-rival measurements, not universal identifiability or a fresh learner-loss evaluation.

Full source-bound receipts, failed intermediate checks and both solve episodes are in this assignment's return ZIP under `checks/` and `solve*/`; top-level `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md` and `RESULTS.json` index them. The post-repair solve is bound to the final generator hash. It matches 3/3 visible examples; both masked inputs execute but correctness is withheld.

### Corrections to the inherited note

Imported note `GNOTE-000226` in `evidence/associated_notes.jsonl` is retained unchanged as historical evidence. Its 0.4251 learner loss was not rerun on this version. Its “D4 transforms do NOT commute” claim is incorrect for this rule: supported Racket application verified 48/48 rotations/reflections over six base scenes (three distinct canonical scenes and three geometric controls). Geometry and frame writes rotate/reflect together. This measured correction does not imply unrestricted permutation of frame/background colors.

The inherited “strict” rates described the coarser morphology signature; they are not rates for the new proximity-inclusive empirical predicate. Historical `workspace/rival-analysis/FINDINGS.md` and snapshots remain tied to the original baseline and early two-rival exploration. Use the current dynamic tools in `workspace/` for new verification.
## Current reviewer considerations

Source SHA-256: `a7ed8b0d8fb5985134246f0b7d928ee5060461a8b08cb7ff9a7c7372765599cf`.

# Decisions — e937c5b85cdd / review-623ff21514220397

## Evidence basis

The immutable selected baseline was generator SHA-256 `25b0edefd8fe5333c0d4d9ac13be097dc2fc59123cf13b5e5c4505014f014b4e`, version 4.2.0, rule hash `538497122a9d`. Prior return `review-10a65405aae36591` was used as a map to retained rivals and historical rationale, not as current evidence. I reran the baseline battery and all final acceptance checks on this packet's bytes.

## D1 — Preserve the canonical generation and teaching distribution

**Choice.** Do not alter the framed-cross grammar, palette roles, four-profile ordinary schedule, three-demonstration policy, or Racket rule.

**Rationale.** The assignment priority asked for a parametric extension first, not gratuitous production churn. The pinned v4.2 baseline already passed rule, authority, distribution, profile, semantic, diversity, override, grammar, and Racket checks. Its only blocking stage was strict malformed-call handling. A fresh 100-lessons-per-band census on the final source materialized 300/300 lessons and found zero ambiguity among 1,200 production pairs and 1,200 query rotations against all three declared rivals.

**Alternatives rejected.** Reweighting profiles, adding more teaching slots, or altering object geometry could increase unsupported correlations and would change deterministic draws without a measured defect. Reducing demonstrations below three or allowing multiple queries has no retained teaching guarantee. Exact override and fixed-texture calls intentionally do not inherit the ordinary schedule's rival-refutation guarantee.

**Limits.** The finite census cannot exclude undeclared rivals or prove learner identifiability. It measures the real sampler with three ordered demonstrations and one query, plus one holdout rotation for each of four materialized pairs.

## D2 — Validate direct call scalars at the task boundary

**Choice.** Add `_validate_call_arguments(seed, sample_index, difficulty)` and call it before `gen_ctx` or override processing.

**Contract.** `seed` must have exact type `int`; `sample_index` must have exact type `int` and be nonnegative; `difficulty` must be `None` or one of `easy`, `medium`, `hard`. Booleans, numeric strings, floats, negative indices, misspelled bands, and non-string band values raise `ValueError` with the relevant argument name.

**Rationale.** Python's `bool`/`int` relationship and the existing fallback band selection let malformed inputs alias lawful tuples. A direct generator API should be reproducible and falsifiable independently of the public wrapper. The same defect class appeared independently in audit target `efdd2b265cc8`, which strengthens the case that it is a systematic generator-boundary risk.

**Alternatives rejected.** Coercing strings/floats would create hidden aliases and inconsistent seeds. Validating only in the public runtime leaves direct task tests and authoring tools exposed. Moving this review's fix into shared code would exceed the selected-task patch scope; `FEEDBACK_TO_CODEX.md` proposes a shared portable helper separately.

**Failure modes and probes.** The fail-first tests cover 5 invalid seeds, 6 invalid sample indices, 7 invalid difficulty values, and four valid difficulty values. The final defect linter is green. A 12-case before/after hash snapshot covering all bands, `None`, multiple seeds/indices, and representative exact overrides found no valid-draw change.

## D3 — Keep `VERSION = 4.2.0`

**Choice.** Do not bump the generator's semantic version for this patch.

**Rationale.** The output rule, valid input domain, distribution, schedule, Racket authority, and valid deterministic samples are unchanged. The patch rejects values that were never lawful API inputs; source identity is already bound by SHA-256 throughout the review system.

**Alternative.** A version bump would be defensible under a policy that versions every source/API change, but it would signal changed valid sampling semantics and could unnecessarily fragment retained evidence. Future maintainers can adopt a global versioning rule if desired.

**Limit.** Consumers that intentionally relied on malformed calls will now fail loudly; that is the desired incompatibility.

## D4 — Add one binary parametric rule prototype, isolated from production

**Choice.** Implement `projection_polarity ∈ {opposite, facing}` under `workspace/parametric/`. Select it exactly once per episode and generate three demonstrations plus one query using the existing framed-cross input grammar.

**Why this parameter.** It preserves the original objects, longest-arm detection, projection axis, and endpoint-writing structure. Only the semantic polarity of the projection changes. The original `opposite` setting is byte-for-byte the canonical Racket program. The `facing` setting is an exact one-fragment action swap, not a Python-only labeler.

**Evidence design.** The prototype strips the outer rule wrapper, binds the grid, and explicitly applies the materialized lambda through `RacketBridge`; merely evaluating the lambda would return a procedure object rather than a label. Public episodes omit the parameter, program, seed, and query output. Tests require the default to match canonical outputs, both settings to be reachable/deterministic, both programs to execute, all three demos to refute the alternate setting, the query to differ, and the evidence manifest hashes to match.

**Alternatives rejected.** Changing arm-length threshold, color-role semantics, or frame/background colors would alter object grammar or domain cues rather than isolate a small rule parameter. A per-object polarity would not be one coherent episode-level rule. More than one parameter was unnecessary for this assignment and would make identifiability harder to attribute.

**Limits.** Evidence is two deterministic episodes (seeds 731 and 735), one binary parameter, and one explicit rival. It is a proposal, not selected-source or training approval. No learner experiment establishes that the latent setting is difficult or useful.

## D5 — Preserve Racket authority

**Choice.** Make no canonical or base-solution edit.

**Rationale.** Rule smoke, authority synchronization, Racket lint, canonical examples, and the parametric default all bind to rule hash `538497122a9d`; canonical program SHA-256 is `ab0d4ff4a785fc9cfe6a0ad81dea9daab643a1c1d32fd5cd9d26aa231649c94c`. The defect is entirely in Python call validation.

**Failure mode avoided.** Changing Racket to accommodate a Python API defect would alter labels and invalidate prior teaching evidence without addressing the boundary issue.

## D6 — Retain interrupted and failing evidence

**Choice.** Keep the completed baseline failure, fail-first pytest output, and both interrupted battery attempts alongside their hash-verified resumed completions.

**Rationale.** A controller interruption is not a pass, and deleting it would obscure the execution history. The `--resume` mechanism verified unchanged source/runtime/checkpoint identities before using completed stages. Final acceptance is based only on completed summaries.

## D7 — Keep audit findings separate and unpatched

**Choice.** Report `72d67c0cf1b7` and `efdd2b265cc8` in `AUDIT.md` with source-bound reproducers, but do not modify either target.

**Rationale.** The assignment explicitly makes these findings-only adversarial reviews. Mixing their repairs into the selected task patch would violate scope and make intake attribution ambiguous.

## Stopping decision

The selected defect has a fail-first regression, a minimal repair, unchanged valid-draw evidence, a 12/12 final battery, a fully green portable task stage, a broad lesson census, an isolated runnable parametric proposal, both required solve records, and two reproducible audit sections. No selected-task blocker remains; remaining limitations are research questions rather than failed acceptance gates.
