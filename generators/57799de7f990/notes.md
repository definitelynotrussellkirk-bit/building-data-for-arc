# Working notes: 57799de7f990

## Current rule and domain

A marker is a zero-valued cell whose four orthogonal neighbours are color 2. For every row and column, the selected rule fills zero cells with color 1 between consecutive aligned marker centers. Inputs are rectangular 9–26 by 9–26 zero-background grids with 3–7 complete diamonds; input colors are restricted to 0 and 2.

## Review `review-2e85e418fcf66580`

The selected `2.0.1` sampler advertised controls it did not honor, silently accepted unknown/invalid arguments, validated red-cell counts instead of complete diamonds, and mostly emitted a regular coarse lattice. That distribution taught an axis-local shortcut: treat a horizontal center as two horizontal arms plus either vertical arm (and analogously for vertical connections). This rival fits all four usable canonical pairs but disagrees on the retained three-diamond witness at `counterexamples/review-2e85e418fcf66580-three-arm/counterexample.json`.

Version `3.0.0` replaces the old lattice controls with four exact observable axes: `grid_h`, `grid_w`, `n_diamonds`, and `three_arm_witness`. Defaults are strongly weighted toward canonical shapes while preserving the full declared range. Consecutive sample indices alternate witness and plain profiles, so every ordinary three-example lesson contains both. Witness geometry spans the long canvas axis; plain geometry spans both axes. The validator now checks exact scalar types, rejects unknown keys, reconstructs complete diamonds, rejects stray red cells, enforces 3–7 markers, and requires a visible transformation.

The selected Racket behavior did not change. Its active `target_code` text was synchronized to the canonical program only after a 284-input execution-parity probe found zero output differences; archival `raw_code` remains unchanged. The canonical `RULE_HASH` is pinned as `cd5434186fae`.

Evidence: final generator SHA-256 `9d5ff588c78e47ab5c094cdb86babc20b20067c092e3a6ba3829942bc72e7681`; 12/12 after-battery stages green; 68/68 portable task tests; 5,040/5,040 exact override cases accepted; profile floor 51/60 exact hits; and 300 materialized lessons with 1,200 required query rotations, zero declared-rival ambiguities, and 671 unique inputs. The prior retained review used as a lead was `review-10a65405aae36591:v0001`.

## Known limits

The curriculum evidence is finite: it refutes the declared axis-local rival and the shared generic rivals, not every conceivable rule. Colors remain fixed to semantic roles 0/2/1, and the generator intentionally covers only 3–7 markers and 9–26 cell dimensions. The owner accepted this exact revision under the lightweight reviewer-reported policy; its exact-source approval is recorded separately. These reported checks were not rerun by the maintainer, and generator approval does not admit model trajectories to training.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-10a65405aae36591:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `dea92c3a98f73a911c052af178d8f4a10766fa24c6c82ea8f6ffcb37ce20b570`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted reviewer-reported v3.0 repair at 9d5ff588c78e47ab5c094cdb86babc20b20067c092e3a6ba3829942bc72e7681 explicitly honors dimensions, replaces inert lattice/fill/texture controls, validates complete markers and samples alternating three-arm witnesses. Retains named counterexample and regression; 68 tests,5040 exact overrides,300 lessons/1200 rotations reported clean. Resolves this compound old-source finding only, not every possible rival or new maintainer verification.

### Assessment or prior finding

## 57799de7f990

**A57799-3 — Reproduced defect: explicit declared-valid dimensions are ignored.** `generate(0, 0, difficulty="hard", grid_h=12, grid_w=12)` returns **24×23**, although both requested dimensions are within the declared `AXES` range `12..26`. Its grid is identical to original case 2, generated with the same seed/index/difficulty and no overrides. The returned input passes `self_check`, and Racket execution succeeds. This is an input-generation contract defect, not a wrong reference label. Source inspection also finds `lattice_step` and `fill_frac` overrides unread, but only the dimensions were reproduced. See [override-probe.json](checks/audit/57799de7f990/override-probe.json) for the exact request, input, validator status, output and hashes; [override-racket.json](checks/audit/57799de7f990/override-racket.json) is the separate authority receipt. Suggested repair: resolve declared overrides before default difficulty draws and handle their bounds explicitly.

**A57799-1 — Domain question / metadata mismatch.** `AXES['texture']['valid']` advertises `one_diamond`, but `generate(0, 0, texture="one_diamond")` produces four red cells and `self_check` rejects it: `only 4 color-2 cells — may be fewer than 2 diamonds`. Racket succeeds and leaves the input unchanged. Because `DEGENERATE_TEXTURES` may intentionally include invalid examples, the rejection alone is not a rule defect. Clarify whether ordinary-valid texture metadata should distinguish validator-rejected degenerates. Exact witness: case 12 in [probe.json](checks/audit/57799de7f990/probe.json).

**A57799-2 — Suspected shortcut / domain limitation.** An intentional three-arm rival recognizes horizontal centers from left/right red arms plus either vertical arm, and vertical centers from up/down arms plus either horizontal arm. It fits **4/4 canonical pairs, 12/12 ordinary generated samples, and 3/3 declared degenerate fixtures**. The generator declares neither `CANONICAL_SHORTCUTS` nor `LESSON_COMPETITORS`; this is an independently tested hypothesis.

Case 15 refutes it: three intact, disjoint diamonds centered at zero-based `(3,3)`, `(4,6)`, and `(3,11)` in a 13×17 grid create a false three-arm center at `(3,5)`. Racket writes `1`; the rival leaves `0`. The input passes the target validator but is **outside the documented coarse-lattice domain**. It therefore establishes a distribution limitation, not an in-domain semantic disagreement. Whether irregular, closely spaced disjoint markers should be sampled remains a domain decision. Exact inputs and rival/reference outputs are in [probe.json](checks/audit/57799de7f990/probe.json), with [racket.json](checks/audit/57799de7f990/racket.json) recording authority execution.

**Rejected hypothesis / No issue found for the simpler two-arm rival.** The preceding axis-local rival fits only **16/20** inputs: generated case 9, handmade case 15, and canonical cases 17 and 19 refute it. It is not claimed as a canonical shortcut; its unsuccessful results remain in [probe-axis-local.json](checks/audit/57799de7f990/probe-axis-local.json).

**Scope.** Original batch: **20 cases / 20 unique inputs**, comprising seeds `0..3`, sample index `0`, each of easy/medium/hard (12 ordinary samples), three declared degenerates, one handmade domain probe, and four canonical pairs. All **20/20** reference executions succeeded; **4/4** reference outputs matched canonical labels; **19/20** inputs passed the validator. The separate dimensions follow-up adds one evaluated case duplicating original case 2: combined totals are **21 cases / 20 unique inputs**, **21/21** successful reference executions, and **20/21** validator passes by case. Rival denominators remain the original batch. No battery, broad sweep, lesson-identifiability, or rotation claim. [commands.json](checks/audit/57799de7f990/commands.json) retains actual cwd/argv/exit codes and the corrected initial probe syntax failure; replayable probes and failed source remain beside it.

Generator version **2.0.1**, SHA-256 `dea92c3a98f73a911c052af178d8f4a10766fa24c6c82ea8f6ffcb37ce20b570`; executed/catalog rule hash `cd5434186fae`; rule-text SHA-256 `838976dadfd5fb6a3e5aa17c991ae9c1d940011254710ad55db53ffcde2b1f99`. Audited source and authority unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-10a65405aae36591-v0001/audit_assets.json), manifest SHA-256 `eb414a20bd255276a7fcf15f29357fdfe78830e9aec090e963244b897ab474d7`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `9d5ff588c78e47ab5c094cdb86babc20b20067c092e3a6ba3829942bc72e7681`.

# Decisions: 57799de7f990

## D1 — Replace the old lattice surface with four exact controls

**Prior choice.** Version 2.0.1 advertised `grid_h`, `grid_w`, `lattice_step`, `fill_frac`, `palette_size`, `position_bias`, and `texture`. Some were singleton/dead, some were not routed through keyed draws, and unknown or invalid values were accepted.

**New choice.** The supported surface is exactly `grid_h` 9–26, `grid_w` 9–26, `n_diamonds` 3–7, and Boolean `three_arm_witness`. Calls reject unknown keys, booleans masquerading as integers, invalid difficulty values, and out-of-domain values through the shared draw contract.

**Rationale and alternatives.** Keeping `lattice_step` and `fill_frac` would preserve superficial compatibility but encode implementation details rather than semantics, and neither naturally describes the irregular witness family. Singleton `palette_size=2` and `position_bias=lattice` were not controls at all. The new axes describe visible output facts and are independently observable.

**Probe/failure mode.** `checks/after/checks/57799de7f990_after_override_results.json` exhausts the declared Cartesian plan: 5,040 accepted cases, no findings or warnings, and the unknown-key probe rejected. The domain deliberately does not expose arbitrary palettes because colors 2 and 1 are semantic.

## D2 — Weight defaults toward canonical profiles without collapsing exact support

**Prior choice.** Difficulty bands selected broad size intervals (easy 12–15, medium 15–20, hard 20–26), which made canonical sizes uncommon and caused the profile gate to be advisory/failing.

**New choice.** All bands retain exact size support 9–26, but each sample index is strongly weighted toward one of the four canonical `(height, width)` profiles: `(14,16)`, `(10,15)`, `(12,15)`, `(9,15)`. Diamond count remains an exact 3–7 control with difficulty-dependent default anchors.

**Rationale and alternatives.** Hard-clamping every draw to canonical shapes would pass profile checks but destroy useful support. Uniform 9–26 support was too weak for the required floor. Weighted exact draws preserve both.

**Probe/failure mode.** Final profile evidence is 51/60 exact hits: easy 16/20, medium 17/20, hard 18/20, with zero crashes or canonical rejection. Large noncanonical dimensions remain reachable through exact overrides and default tails.

## D3 — Alternate witness and plain profiles by sample index

**Prior choice.** The coarse-lattice sampler generated lawful labels but did not reliably distinguish complete diamonds from an axis-local three-arm recognizer.

**New choice.** `schedule_profile` alternates `three_arm_witness`, `plain` with period 2, independent of seed and difficulty. The exported lesson uses three consecutive demonstrations and one query, so ordinary production demonstrations contain both profiles. Query-rotation checks hold out each of the four labeled pairs once.

**Rationale and alternatives.** Pure rejection sampling for a witness could make lesson support probabilistic; forcing every input to be a witness would narrow the distribution and teach a new artifact. Alternation gives deterministic coverage while retaining neutral examples.

**Probe/failure mode.** The canonical-fitting rival is refuted in 100/100 lessons per band in production and in every required rotation. The result is finite-rival evidence only; undeclared rivals remain unknown.

## D4 — Use explicit irregular geometry rather than a coarse lattice

**New choice.** Plain layouts embed a seven-point index pattern into three gapped rows and columns spanning the canvas, with all dihedral orientations. Witness layouts place the first and third diamonds near opposite ends of the longer axis and choose among eight lawful suffixes, with independent mirrors and short-axis offset.

**Rationale and alternatives.** A general random backtracker would add complexity and make exact replay/debugging harder. A single fixed witness would be easy to memorize. Small constructive families are deterministic, exact-control friendly, and still diverse.

**Probe/failure mode.** The first long-axis prototype caused added diamonds to paint one another's centers; the focused test caught it. The final seven-center sequence preserves the exact diamond count for every 9–26 dimension and keeps at least 2% of cells transformed on 9×26, 26×9, and 26×26 three-marker examples. Evidence: `checks/tdd-green-transform-strength.log`.

## D5 — Validate structure, not color counts

**Prior choice.** `self_check` accepted grids based mainly on having enough color-2 cells.

**New choice.** Reconstruct complete four-arm centers; require zero-valued centers, exactly 3–7 diamonds, every red cell owned by at least one complete diamond, only colors 0 and 2, dimensions 9–26, and at least one visible connection.

**Rationale and alternatives.** Counting red cells cannot distinguish a legal marker set from stray fragments or overlapping impostors. Reusing the selected Racket implementation would couple validation to authority internals, so the Python structural logic is independent and cross-checked by task-local tests.

**Known limitation.** The validator intentionally rejects lawful instances outside the generator's declared 3–7 marker and 9–26 size domain; it is a generator-domain validator, not a complete recognizer for all possible ARC inputs.

## D6 — Synchronize selected authority text without changing behavior

**Prior choice.** The selected `target_code` was a behavior-equivalent alias/formatted variant of the canonical program, while archival `raw_code` retained the imported source.

**New choice.** Preserve `raw_code`; replace only active `target_code` with the exact canonical program text.

**Rationale and alternatives.** Leaving the divergence made the mandatory authority stage fail. Rewriting the canonical source or changing the rule was unjustified. Before synchronization, `checks/authority_parity-before.json` exercised 284 inputs and found zero output mismatches.

**Result.** The selected JSON changed text but not semantics. The rule hash remains `cd5434186fae`; final rule smoke, Racket lint, and authority sync are green.

## D7 — Retain independent task-local tools and counterexample

`workspace/reference_probe.py` provides a portable independent geometry oracle, canonical-pair loader, observable-axis extractor, and the axis-local rival without importing production helpers from `generator.py`. The minimal exact witness and expected differing cells are retained under `counterexamples/review-2e85e418fcf66580-three-arm/` and covered by focused tests. This gives future reviewers a runnable starting point rather than only prose.

## D8 — Stop after green required checks, one honest solve, and two reproduced audits

The final source passed the complete 12-stage after battery, 68 portable task tests, and the 300-lesson census. The visible-only solve passed 3/3 demonstrations on its first revision; private labels remain withheld. Further widening to arbitrary colors, dimensions, or marker counts would be a new domain decision rather than a repair, so it was not added.

## Review `review-f4f180f77149a955` — isolated parametric prototype

The selected canonical generator remained version `3.0.0`, SHA-256 `9d5ff588c78e47ab5c094cdb86babc20b20067c092e3a6ba3829942bc72e7681`; no canonical source or Racket authority was changed. Fresh before and after batteries each passed 12/12 stages, standalone lint passed, and the portable task snapshot passed 74/74 tests. A new 100-per-band lesson census materialized 300/300 production lessons with 1,200/1,200 production pairs and 1,200/1,200 required query rotations, zero declared-rival ambiguities, and 671 unique inputs (`checks/lesson-census-parametric-review.summary.json`).

A proposed task-local extension now lives under `workspace/parametric/`. It fixes one hidden `axis_mode` per episode: `both` (the exact canonical/default Racket bytes), `horizontal`, or `vertical`. All modes preserve complete-diamond recognition, consecutive aligned-center logic, input preservation, and color roles; the variants disable only the opposite direction’s adjacency branch. Three retained episodes each contain three demonstrations and one query, every input exposes both connection axes, and exact Racket execution distinguishes the chosen setting from both rivals before the query. Focused tests pass 6/6; exact rule hashes and public/private episode evidence are in `checks/parametric/axis-mode-v1/report.json`.

Decision: keep this extension labeled `prototype` and separate from `generator.py`, canonical authority, and approval metadata. Its controlled fixtures establish exact-default preservation and bounded parameter identifiability, not production distribution breadth, universal uniqueness, or training admission. Promotion would require a broader sampler, additional plausible rivals, schedule policy, and owner approval.
