# Working notes: a0ff437161da

## Current rule and source identity

- Final generator version: `4.2.0`
- Final generator SHA-256: `83ea2c0febdad3b0712bfb0cabbf3e0f14695125c5099285feb641edff6eb25c`
- `RULE_HASH`: `c70fab479c5e`
- Canonical Racket source SHA-256: `48130e6e8cb3ee0d8fc1f84e79c4fe052a9cfd0728effa34f7bde67da7e8b8b8`

On literal background 8, find the first non-8 cell in row-major order. Fill the inclusive rectangle from that marker to a Manhattan-nearest corner with the marker color. Exact ties use `UL, UR, LL, LR` priority.

## Repair decisions

Version 4.0 sampled profiles independently. Although its individual pairs were lawful, a three-demo lesson could omit a witness to the tie priority. Version 4.2 uses a 36-slot default schedule alternating tie and non-tie profiles. Every cyclic four-pair lesson contains exactly two tie witnesses, so every one-query rotation leaves a witness in the demos when reverse tie priority changes the query.

An intermediate repair concentrated color 9 on tie cases. It refuted the shared `first_color_only` search rival but reduced 3,000-draw uniqueness below the retained floor and coupled color with geometry. The final independent marker cadence is `9,9,<9,<9`; each four-pair window contains two color-9 and two non-9 examples. Explicit profile overrides keep the full marker palette and do not use the forced cadence.

Both default and explicit profile selection go through keyed `scene_profile` provenance. Public generation rejects unknown overrides and requires exact integer `seed`/`sample_index` in `[0, 2**63)`.

## Semantic contract

`reverse_tie_order` (`LR, LL, UR, UL`) fits all five labeled canonical pairs because they contain no nearest-corner ties. It is declared in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, and `LESSON_COMPETITORS`. `lesson_identifiable` requires at least three demos and rejects any declared rival that fits every demo but changes the query.

Minimal retained witness: `counterexamples/review-cac633488d9764e2/reverse_tie_order.json`. Exact generation recipe: easy, seed 1730, sample index 0, explicit `top_tie`. Canonical and rival outputs differ on 12 cells.

## Authority decision

Selected base `target_code` now equals canonical `program_solution` byte-for-byte. Archival minified `raw_code` remains unchanged and normalized-equivalent. This repairs source synchronization without changing Racket behavior.

## Verification snapshot

- final full battery: 12/12 green (`checks/after-final/`)
- portable task tests: 40 passed (`checks/task-tests-final/`)
- lesson census: 300/300 materialized, 0 production ambiguities, 0/1,200 ambiguous rotations, 987 unique inputs (`checks/lesson-census.json`)
- task-local schedule proof: all 36 starts × all four query positions for reverse tie and the retained shared search rival
- post-repair visible solve: 3/3 on first revision, earlier exposure disclosed (`solve/`)

## Parametric extension

`workspace/parametric/prototype.py` proposes episode-level `tie_order` with canonical `ul_ur_ll_lr` and alternative `lr_ll_ur_ul`. Both exact Racket settings execute, both seeds produce identifiable 3-demo/1-query episodes, and canonical default replays all five labeled pairs. Status is `proposed_unapproved`; it is not part of canonical approval.

## Known limits

The default curriculum is structured, not IID, and exposes sample-index cadence. Finite checked rivals do not establish universal identifiability. `LESSON_SCHEDULE_PERIOD` is not declared; exhaustive period evidence currently lives in task tests rather than the shared period enumerator. The shared generic color rival conflates nonzero background 8 with object colors; feedback requests role-aware candidate generation.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-a0c2189a1767a9f8:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `cdf3c2a102e88d37898e38380caab0afa0e036a60950fe08350e2ed8629c84da`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve selected-authority byte drift andmissing semantic-contract finding. Selected target_code now equals unchanged canonical text;owner static comparison confirms Rackettokens,archival raw_code andeveryother JSON field unchanged. New tie/color witness schedule anddeclared rivals report300lessons/1200rotations clean,40portable/fresh tests and12/12battery. No semantic authority change oruniversal induction claim.

### Assessment or prior finding

## a0ff437161da

**Reproduced authority-text divergence; no behavioral mismatch found in the
profile spot-check; no fix applied.** Generator SHA-256
`cdf3c2a102e88d37898e38380caab0afa0e036a60950fe08350e2ed8629c84da`.
The full baseline battery finished with 10 green, 1 advisory, and 1 failed stage.
The semantic gate had no contract; `authority_sync` failed because active
canonical and selected target-code authorities differ in exact source text.
Execution parity nevertheless passed across the two distinct sources. Evidence:
`checks/audit-battery-a0ff437161da/checks/a0ff437161da_before_battery_summary.json`
and its authority-sync JSON/log.

I then generated one deterministic hard-band sample for each of nine generalized
nearest-corner relation profiles: four unique nearest corners, top/bottom/left/
right ties, and a four-way tie. All nine generator outputs were valid and matched
the executed Racket output. The complete profile metadata and hashes are in
`checks/audit/a0ff437161da/profile-audit.json`; raw inputs and Racket outputs are
retained in the same directory.

The reproduced issue is therefore source-governance ambiguity, not an observed
semantic error. The nine-case test is a bounded spot-check, not proof that every
lawful relation profile is correct, and the missing semantic contract remains a
training-data limitation.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-a0c2189a1767a9f8-v0001/audit_assets.json), manifest SHA-256 `77b0af7f0054b1d2b5859206da70fc6c290721f69d451efd4316d684486e04f0`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `83ea2c0febdad3b0712bfb0cabbf3e0f14695125c5099285feb641edff6eb25c`.

# Decisions for `a0ff437161da`

## D1 — Preserve the canonical rule exactly

**Choice.** Treat color 8 as literal background; use the first non-8 cell in row-major order; fill the inclusive rectangle to a Manhattan-nearest corner; resolve ties `UL, UR, LL, LR`.

**Rationale.** The selected Racket authority, five labeled canonical pairs, and existing generator summary agree on these semantics. The canonical examples do not exercise ties, so tie order is an authority-bound detail rather than an inference from the labeled pairs.

**Alternatives rejected.** Reversing tie order, choosing the geometrically largest rectangle, or randomizing ties all fit the labeled no-tie pairs but contradict the authority on generated tie witnesses.

**Evidence/limits.** Canonical source SHA `48130e6e…8b8b8`; normalized `RULE_HASH=c70fab479c5e`. The retained rival demonstrates why no-tie canonical examples alone are insufficient.

## D2 — Make lesson semantics, not individual-pair correctness, the scheduling unit

**Prior choice.** Version 4.0 independently sampled a weighted mixture of exact-public, unique-corner, and tie profiles. It generated lawful pairs but gave no guarantee that the three demonstrations refuted a query-changing tie rival.

**New choice.** Use a deterministic 36-slot profile schedule. Tie and non-tie profiles alternate, so every cyclic four-pair window contains exactly two direct tie witnesses. Any one of the four positions may be the query; the remaining three demos still contain a tie witness whenever reverse tie order changes that query.

**Why 36.** It is long enough to include all 14 declared scene profiles, all five tie geometries, all four unique-corner geometries, and all five exact public profiles while retaining the alternating invariant.

**Alternatives rejected.** Merely raising tie probability leaves nonzero probability of an ambiguous complete lesson. Forcing every example to be a tie would teach the branch but collapse useful geometry and distribution support.

**Evidence/limits.** Task tests exhaust all 36 starts and four query positions. `LESSON_SCHEDULE_PERIOD` is not declared, so the shared census does not claim formal period enumeration; this is documented rather than overstated.

## D3 — Balance semantic witnesses with marker-color nuisance support

**Failed intermediate choice.** A first rotation-safe schedule concentrated color 9 on tie examples. It refuted the searched `first_color_only` rival but reduced diversity (2,127 unique inputs in the 3,000-draw probe, below the retained >2,200 floor) and coupled color with geometry too strongly.

**New choice.** Independently cycle default marker behavior as `9,9,<9,<9`. Every four-example window has two color-9 witnesses and two non-9 examples. Tie/non-tie alternation is separate, so non-9 tie counterfactuals and color-9 non-tie counterfactuals remain available.

**Explicit overrides.** An explicit `scene_profile` keeps the full marker palette `{0,1,2,3,4,5,6,7,9}` and is not forced by the curriculum cadence.

**Evidence.** Final 3,000-draw test exceeds 2,200 unique inputs/outputs, spans >150 shapes and >40 rectangle areas, and observes all marker colors and all selected corners. The 300-lesson census finds 987 unique inputs.

## D4 — Declare the strongest canonical-fit rival as executable code

**Choice.** `reverse_tie_order` uses the same marker, distance metric, rectangle fill, and corner set, but tie priority `LR, LL, UR, UL`.

**Rationale.** It fits all five labeled canonical pairs, changes only the unexercised tie branch, and disagrees on every declared tie profile. It is stronger than a train-only shortcut such as “never choose lower-right,” because that weaker rule is already contradicted by the labeled canonical test pair.

**Integration.** The function is shared by `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, and `LESSON_COMPETITORS`; `lesson_identifiable` rejects a lesson if a declared rival survives all demos and changes the query.

**Limit.** This is the strongest plausible rival checked, not an exhaustive characterization of all programs fitting the canonical pairs.

## D5 — Retain a minimal, source-bound counterexample

**Choice.** Keep a 7×7 top tie with color 1 at `(1,3)` in `counterexamples/review-cac633488d9764e2/reverse_tie_order.json`.

**Exact generation recipe.** `seed=1730`, `sample_index=0`, `difficulty=easy`, `scene_profile=top_tie`.

**Outputs.** Canonical fills rows `0..1`, columns `0..3`; reverse priority fills rows `0..1`, columns `3..6`; 12 cells differ.

**Verification.** Canonical and alternative Racket sources execute this fixture in `checks/parametric/tie-order/private/episode-000.json` and `episode-001.json`. A portable regression reconstructs the exact grid/outputs without depending on optional documentation files.

## D6 — Enforce strict generation scalars at the public boundary

**Choice.** Require exact `int` (not `bool`) and `0 <= value < 2**63` for both `seed` and `sample_index`.

**Rationale.** The baseline defect lint showed `sample_index=-1` was accepted. Booleans are Python integers but are not valid generator identities. Failing before context construction makes behavior uniform and debuggable.

**Alternatives rejected.** Silent coercion or modulo normalization would alias distinct invalid calls to valid episodes and obscure provenance.

## D7 — Preserve keyed provenance for scheduled defaults

**Choice.** Both explicit and default profile selection call `ctx.draw_choice("scene_profile", ...)`; the default uses a singleton containing the scheduled profile.

**Rationale.** Directly bypassing the keyed draw made behavior correct but failed the override/provenance gate. The singleton draw records the same semantic axis without introducing randomness.

**Evidence.** The intermediate full battery retained the failure; `checks/override-final/` and the final battery pass.

## D8 — Synchronize selected authority text, preserve archival source

**Choice.** Set selected `racket_target.target_code` exactly to canonical `program_solution`; keep `raw_code` untouched.

**Rationale.** Execution and normalized text already matched, but byte divergence caused authority synchronization failure and complicated source binding. Selected execution text should be canonical; archival provenance should not be rewritten.

**Effect.** No rule semantics changed. Final authority sync records target equality and execution parity, while the test asserts `raw_code != target_code` but normalized equivalence.

## D9 — Make task tests portable

**Prior choice.** Inherited tests guessed fixed parent depths and imported repository-private paths. Portable preflight failed before pytest.

**New choice.** Use `reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, and `load_selected_generator`. Do not import private per-puzzle aliases.

**Counterexample portability.** A later test initially opened the retained JSON from `counterexamples/`; staged runtimes do not copy that directory. The failed run is retained. The final test always reconstructs and verifies the exact recipe/grid/outputs and conditionally cross-checks the JSON in a full checkout.

## D10 — Parametric extension varies only episode-level tie priority

**Choice.** Prototype parameter `tie_order` has two values: canonical `ul_ur_ll_lr` and alternative `lr_ll_ur_ul`, selected once per episode.

**Why suitable.** It changes a coherent, local branch of the reasoning process while keeping marker discovery, distance, rectangle construction, and color semantics invariant. Tie fixtures make the setting inferable from three demos.

**Why not canonical.** The task authority fixes `UL, UR, LL, LR`; the alternative is a proposed family variant, not a repair. Evidence is marked `proposed_unapproved`, and public challenges omit parameter/source/query-answer metadata.

## D11 — Preserve failures and separate audit scope

The interrupted baseline, completed baseline failures, intermediate semantic/override failures, and counterexample portability failure are retained. Audit targets `04b1a77fc994` and `b9d914a60205` were inspected and reproduced at their assigned source hashes but not edited, because the assignment requests evidence rather than repairs for those targets.

## D12 — Stop after complete final evidence

The final source passes all 12 battery stages, 40 portable tests, the 300-lesson/1,200-rotation census, parametric execution, and the visible post-repair solve. Remaining uncertainty is explicitly epistemic—finite rival checks do not prove universal identifiability—not an unverified implementation blocker.
