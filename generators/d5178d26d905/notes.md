# Working notes: `d5178d26d905`

## Current account — version 2.1.0

The intended rule parses a full color-5 divider, a 0/4 reference panel, and a colored template panel. The sparsest positive-yellow reference row identifies output line columns; denser reference rows are special rows. The template modal row supplies the line colors, and other template rows supply special fill/retention variants. Special rows are paired **top to bottom**.

Version 2.1.0 repairs the unresolved same-source teaching defect retained from `review-ccacfd8306e55d7a:v0001`, `review-3afe572ef1d56c81:v0001`, and `review-bb05e49bfe39011c:v0001`. A plausible rival sorted special rows by yellow-marker density. It fit all 10 canonical records and previously survived a real three-demonstration production lesson while changing the query.

Current source SHA-256: `2e9e935392918e4601d5a435bd25dd54644694bb936161335e11ad39191990ca`. Selected Racket rule hash: `70d9964daef1` (unchanged).

## Current repair

- Declare `yellow_density_order` in every semantic rival inventory and link it to an executable witness.
- Generate noncanonical marker patterns whose density order differs from row order; every supported noncanonical role independently refutes the rival.
- Extend `workspace/reference_probe.py` with an independent density-order implementation.
- Reject Boolean, non-integer, and negative schedule scalars before profile selection.
- Preserve the canonical production rule and existing visible controls.

The stable six-start schedule repeats the three semantic roles `canonical_scale`, `third_special`, and `variable_width` while side/alignment and other geometry vary across starts. Canonical samples preserve public-family support; both noncanonical roles refute all three declared canonical-fitting rivals: `first_two_special_rows_only`, `fixed_reference_width_seven`, and `yellow_density_order`.

## Reusable task-local tools

- `workspace/reference_probe.py`: independent parser, intended oracle, and all three rivals.
- `workspace/cyclic_lesson_probe.py`: discovers declared competitors and checks every query rotation.
- `workspace/parametric/prototype.py`: exact-Racket episode generator for `special_mapping_order`.
- `counterexamples/yellow-density-order.json`: compact current-source disagreement witness.
- `tests/test_generator.py` and `tests/test_parametric_mapping_order.py`: 85 focused portable regressions.

## Final evidence

- Exact prior production recipe: accepted indices `[7,8,9,10]`; two demonstrations refute yellow-density ordering; query differs; lesson hook accepts (`checks/repair/d5178d26d905-density-order/report.json`).
- Strict after battery: 12/12 green with all six declared starts enumerated and rotations required (`checks/after-schedule/result.json`).
- Task tests: 85/85 pass (`checks/task-tests/result.json`; a fresh return-handoff rerun is indexed in `RESULTS.json`).
- Large census: 300/300 three-demo/one-query lessons, 1,200 held-out-pair rotations, 1,200 unique inputs, zero declared ambiguity or scoring/materialization error (`checks/lesson-census.summary.json`).
- Cyclic probe: 960/960 rotations over 552 unique inputs (`checks/repair/d5178d26d905-cyclic-rotations.json`).
- Parametric prototype: two complete exact-Racket episodes; every demonstration distinguishes top-to-bottom from bottom-to-top; proposed only (`checks/parametric/d5178d26d905-mapping-order-seed23/receipt.json`).

## Known limits and open findings

No selected-task blocking finding remains on the tested source. Finite named-rival checks are not universal identifiability proofs. Generated special-row counts remain 1–3 and reference widths 5, 7, or 9; the six-start curriculum is deterministic. The parametric reverse-order variant is not approved or wired into production.

# Decisions — d5178d26d905

No prior associated note supplied a design rationale; `evidence/associated_notes.jsonl` was empty. Baseline intent below is therefore inferred from source and canonical examples, not claimed as author testimony.

## D1 — Reconstruct the full structural domain instead of extending the 5×11 special case

**Baseline choice and inferred rationale.** Version 1.1 generated a fixed five-row, two-five-column-panel pattern. It likely captured one visually simple canonical motif, but not the selected rule’s actual structural invariants.

**Decision.** Parse and generate around one full color-5 divider, one 0/4 reference panel, one colored template panel, a uniquely modal template row, a sparsest positive-yellow reference row, and ordered special rows on both sides.

**Alternatives rejected.** I rejected adding more hard-coded canonical shapes to the old constructor. That would improve profile counts without making the validator or rule mirror general, and would preserve a growing collection of shape-specific branches.

**Probe/failure mode.** The baseline rejected all 10 canonical inputs. The final parser accepts all 10 and rejects malformed dividers, ties, line-count mismatches, and inconsistent special-row fills. Evidence: before/final self-check logs and task tests.

## D2 — Publish only controls that can be observed and falsified

**Baseline choice and inferred rationale.** The old API declared `grid_h`, `grid_w`, `palette_size`, `position_bias`, `n_distinct_colors`, `anchor_corner`, and `asymmetry_force` even when their domains collapsed or the returned grid could not prove they were honored.

**Decision.** Keep only `reference_side = left|right` and `template_alignment = top|center|bottom`. Both are exact, recoverable from the returned grid, and tested at every value. Shape, palette, line count, and number of special rows remain internal distribution choices rather than fake public axes.

**Alternatives rejected.** I did not expose `profile`, `reference_width`, or `special_count` as public controls because they are semantic curriculum roles rather than user-facing combinatorial axes. Exposing them would make the teaching schedule easier to bypass and add compatibility combinations with little review value.

**Limit.** `center` is inferred from balanced gray padding; the scheduled dimensions deliberately leave visible slack to keep this observable.

## D3 — Preserve canonical support while adding targeted counterexamples

**Decision.** Use three deterministic profiles:

1. `canonical_scale`: cycles through all five public shape/palette profiles.
2. `third_special`: generates three ordered special rows and a reference width of 5 or 9.
3. `variable_width`: generates a reference width of 5 or 9, four line columns, and three special rows.

Every three consecutive samples contain all three roles. The canonical role prevents a distribution that only tests extrapolation; the other roles break canonical-only assumptions.

**Alternatives rejected.** Pure random sampling could make a small three-example lesson omit a needed witness. A single permanent noncanonical shape would create a new template shortcut. The current profile choices vary height, line count, side, alignment, geometry, and task colors while keeping the semantic witness reliable.

## D4 — Harden every noncanonical profile after the cyclic-query failure

**Initial design.** `third_special` originally targeted only the first-two-special shortcut, while `variable_width` targeted only fixed width seven. Ordinary three-demo/one-query census sampling passed.

**Observed failure.** Rotating each member of a four-example window into the query position produced 4 failing tests: when the only third-special case became the query, `first_two_special_rows_only` survived all demonstrations. Evidence: `checks/cyclic-red/result.json`.

**Final decision.** Both noncanonical profiles independently include three special rows and non-seven width. That redundancy is intentional: any three demonstrations from four consecutive samples still contain a counterexample to each rival.

**Final probe.** 480/480 rotations across default/easy/medium/hard passed; no declared rival survived. Evidence: `checks/cyclic-lesson-probe.json`.

## D5 — Model two explicit canonical-fitting rivals (2.0.0; superseded by D9)

**Decision.** Declare:

- `first_two_special_rows_only`: maps only the first two special row variants and treats later rows as ordinary lines;
- `fixed_reference_width_seven`: forces output width seven.

Both fit all 10 canonical train/test pairs, so they are genuine underdetermination risks rather than arbitrary wrong programs. Their predictions are executable and linked to witnesses.

**Alternative rejected.** I did not inflate the contract with weak rivals that already fail canonical examples. The purpose is to teach distinctions the canonical set cannot establish.

**Limit.** These rivals are not exhaustive. The census result is finite-rival evidence, not universal induction.

## D6 — Use an independent oracle for tests; keep Racket as label authority

**Decision.** `workspace/reference_probe.py` independently re-parses grids and computes expected outputs without calling production generator helpers. Task tests compare generated structures and rival predictions against it. Official labels remain the selected Racket rule and are checked by rule smoke, semantic gate, authority sync, and the explicit shortcut witness.

**Reason.** Testing `rule_mirror` only against itself would allow a shared implementation error. The independent oracle makes parser and mapping mistakes observable, while Racket parity protects against two Python implementations agreeing on the same wrong interpretation.

## D7 — Synchronize the archival Racket spelling, not the behavior

**Observed issue.** Strict defect lint found the augmented task record’s Racket text diverged from the selected canonical source even though normalized execution was behavior-equivalent.

**Decision.** Replace both archival code fields in `repo/shared/data/base/solutions/augmented/b0f4d537__ebdee59d16f1.json` with the exact selected canonical Racket source.

**Alternative rejected.** Suppressing the warning would leave two authorities that reviewers must compare manually. Rewriting the canonical authority was unnecessary and riskier.

**Verification.** Rule hash stayed `70d9964daef1`; authority sync reports no divergent archival source and execution parity `PASS`.

## D8 — Retain failures and build reusable probes

The failed initial contract run, source-divergence lint, cyclic-query failure, and interrupted battery are preserved. `workspace/cyclic_lesson_probe.py` is intentionally reusable by future reviewers; it discovers competitors from the generator declaration rather than copying rival names into the probe.

## Distribution limits

- The three-cycle is deterministic by sample index. This guarantees witness coverage but makes curriculum role periodic; roles are not encoded as cells or labels in the puzzle itself.
- Generated special-row counts are 1–3 and reference widths are 5, 7, or 9. Those bounds cover canonical support and the selected rivals but are not a claim that the abstract rule is limited to them.
- The large census materializes overlapping four-example lesson windows. It produced 1,200 unique inputs, but lesson windows are not statistically independent.
- Finite test, census, and rival evidence cannot prove universal identifiability.

## D9 — Add the yellow-density rival and reverse the retained teaching defect

**Prior choice.** Version 2.0.0 declared only first-two-special and fixed-width rivals. Three independent audits later showed that yellow-marker density supplied another canonical-fitting row order.

**New choice.** Version 2.1.0 declares density order everywhere, makes both noncanonical profiles refute it, and retains the exact old production window as a regression. The strongest current witness is `counterexamples/yellow-density-order.json`.

**Evidence.** The old source reproduced the ambiguity; the new source preserves indices `[7,8,9,10]` while demonstrations 7 and 8 now refute the rival. The 300-lesson census and 960-rotation probe find no declared ambiguity.

## D10 — Validate request scalars without coercion

The prior API allowed `-1` to select the final schedule element and allowed Boolean aliases. Version 2.1.0 rejects non-exact integers and negative sample indices. Coercion was rejected because it would make receipts and scheduler/generator behavior disagree for floats.

## D11 — Propose `special_mapping_order` as the bounded original-family parameter

The separate prototype varies only the top-to-bottom versus bottom-to-top correspondence between special rows. It preserves object roles and all other rule structure. Both settings have exact Racket files and three-demo/one-query episodes that distinguish the setting. It remains outside production and approval.

## D12 — Final self-review

The repair does not encode one fixed counterexample: dimensions, colors, side, alignment, line count, and marker positions continue to vary. The deterministic schedule and finite rival inventory remain limitations; no claim of universal induction is made.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-bb05e49bfe39011c:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e8787dbbef4a4344b0068ad4582da67825b92e0c1937cecedb584aa2c2f986e1`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve yellow-density-order teaching finding on current2e9e9353 repair. Rival is declared/executable andindependentlyimplemented;noncanonical profiles refute density ranking. Exact seed0/medium/start7 stillaccepts[7,8,9,10],nowtwodemos refute rival andquerydiffers. Reviewer85portable tests,12/12schedule-enumerated battery,300lessons/1200rotations and960cyclic rotations reportclean. Canonical Racket unchanged;finite named-rival evidence,notuniversalidentifiability.

### Assessment or prior finding

## d5178d26d905

**A-D517-1 — Reproduced teaching defect: yellow-density ordering fits the demonstrations and changes the query.** This independently reproduces the unresolved same-source lead retained in `review_index.json` from `review-ccacfd8306e55d7a:v0001` and `review-3afe572ef1d56c81:v0001`. Findings only; the audited generator, rule, notes and audit disposition were not changed.

Audited generator v2.0.0 SHA-256: `e8787dbbef4a4344b0068ad4582da67825b92e0c1937cecedb584aa2c2f986e1`. Fresh executed Racket hash: `70d9964daef1`; rule-text SHA-256: `ae54e032083a72a27c45bf985fd073b9fe2299463578d3788697ceb563a5db3c`.

The intended rule pairs special reference rows and special template rows by their top-to-bottom order. The plausible rival instead sorts the special reference rows by increasing yellow (`4`) count, with row position breaking ties, before assigning the template variants. An independently written parser and rival, without the audited generator's private parsing or mirror helpers, fit all **10/10 canonical records, representing five unique inputs**. Every retained canonical label was freshly checked through public `Catalog.apply`; all ten agreed with the Racket result and the independent intended-rule mirror.

**Actual production witness:** seed `0`, difficulty `medium`, requested start `7`, overrides `{}`, three demonstrations and one query. Public `Catalog.generate` returned accepted sample indices **[7, 8, 9, 10] with zero rejections**. All four accepted inputs pass both `self_check` and `strict_canonical_like`; their authoritative outputs agree with the independent mirror. The density-order rival fits all three demonstrations and differs from the query in **10 cells**. Query special rows `[0, 4, 8]` have yellow counts `[4, 5, 4]`, so the rival maps them in order `[0, 8, 4]` and exchanges the variants for output rows 4 and 8.

The existing `lesson_identifiable` hook returns `[]`. Both actually declared rivals are refuted by demonstrations 0 and 1; neither covers density ordering. Thus the positive existing lesson verdict and the measured ambiguity concern different rival inventories. This is a lawful emitted teaching counterexample, not merely a hand-made input admitted by a permissive validator.

**Additional bounded evidence:** 135 generated inputs across seeds `0..2`, indices `0..14`, and easy/medium/hard all passed both validators. The independent Python mirror agreed with the generator mirror on 135/135, and the density rival agreed with that mirror on 134/135. These census labels are Python predictions, not additional Racket executions. Fresh Racket execution covered the ten canonical records and four production-lesson pairs. This audit did not rerun a full battery or measure arbitrary query rotations, and the finite counts are not a prevalence estimate.

**Suggested task-local repair:** declare the density-order competitor, vary marker density independently of special-row position, and ensure each supported demonstration set distinguishes row order from density order whenever its query separates them. Preserve this exact seed/start regression. The retained finding remains unresolved on unchanged bytes.

**Evidence and replay:** `checks/audit/d5178d26d905/evidence.json` retains domain results, current declaration inventory, actual lesson inputs/labels, rival outputs and all differing cells. `canonical-racket.json` retains the public apply receipt; `generated-lesson.json` retains the full public production episode. `probe.py` is the portable reproducer; `query-input.json` and `query-rival.json` are the minimal query artifacts. `commands.json` and `probe.log` record the exact command, working directories, source hashes and exit code **0**, meaning the expected audit reproduction succeeded.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-bb05e49bfe39011c-v0001/audit_assets.json), manifest SHA-256 `ddfaedc7ea26649783a55b7a6631d177116b6d1fd80345ad6f84792a4674202d`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `2e9e935392918e4601d5a435bd25dd54644694bb936161335e11ad39191990ca`.

# Decisions — `d5178d26d905`

## D1 — Reproduce the retained audit lead before editing

Three same-source prior findings (`review-ccacfd8306e55d7a:v0001`, `review-3afe572ef1d56c81:v0001`, and `review-bb05e49bfe39011c:v0001`) identified yellow-density ordering as a canonical-fitting interpretation. I treated them as leads, not measurements of this packet. A fresh baseline probe on SHA `e8787dbbef4a4344b0068ad4582da67825b92e0c1937cecedb584aa2c2f986e1` reproduced the exact seed-0/medium/start-7 ambiguous lesson and found the rival agreed on 134/135 generated inputs (`checks/diagnosis/d5178d26d905-density-baseline/evidence.json`).

Alternative rejected: adding a one-off assertion for only that query. It would prevent one regression while leaving the semantic contract and sampler blind to the underlying interpretation.

## D2 — Promote yellow-density ordering to a first-class rival

The rival now appears in all three public semantic inventories and has a matching witness plus independent oracle. This makes lesson assembly reject a bundle when the rival fits every demonstration and changes a query.

Alternative rejected: rely only on `lesson_identifiable` private logic. Keeping the rival declarative makes the census, semantic gate, tests, and future authoring tools discover it without copying task-specific names.

## D3 — Decouple marker density from row position in every noncanonical profile

Both `third_special` and `variable_width` choose yellow-marker counts whose density order differs from top-to-bottom order. This is deliberately redundant: in a four-pair window, any one pair can become the query and the remaining three still contain a density-order counterexample.

Alternative rejected: reserve the witness for only one profile. The earlier first-two-special repair showed that a sole witness can move into the query under rotation and disappear from the demonstrations.

Limit: the canonical profile continues to match the public family and may not refute the rival by itself; teaching strength comes from the mixed schedule, not by rewriting canonical examples.

## D4 — Preserve the selected Racket authority

The repair changes generation, validation, semantic declarations, tests, and task-local tooling only. The selected Racket rule remains hash `70d9964daef1`, because the reproduced defect was lesson underdetermination rather than a wrong canonical transformation.

## D5 — Reject invalid schedule scalars at the API boundary

`seed` and `sample_index` now require `type(value) is int`, and `sample_index` must be nonnegative. This intentionally rejects Boolean values despite Python’s `bool` subclassing `int`, and rejects floats before list indexing or schedule arithmetic can diverge.

Alternative rejected: coerce with `int(value)`. Coercion would silently alias requests such as `1.5`, hide scheduler/generator disagreement, and make receipts misstate the actual requested index.

## D6 — Keep an independent oracle separate from production helpers

`workspace/reference_probe.py` parses the task independently, implements the intended mapping and all three rivals, and is used by regression/probe code. Official labels still come from the selected Racket authority. Two Python implementations agreeing is not sufficient; the final battery and exact witness retain Racket hashes.

## D7 — Add a bounded original-family parameter, not a new production branch

The prototype parameter is `special_mapping_order = top_to_bottom|bottom_to_top`, chosen once per episode. It preserves the divider, reference/template roles, parsing, colors, and output geometry while varying the central row-correspondence rule. Each setting has a materialized Racket rule and demonstrations that distinguish it.

Alternatives rejected:

- varying divider side or alignment: already generator controls, not rule parameters;
- varying output width: risks teaching a geometry shortcut rather than the original correspondence;
- varying yellow-density ordering: that is a wrong rival to refute, not a desired target variant.

The prototype remains under `workspace/parametric/`; it does not alter the canonical production path.

## D8 — Require explicit schedule enumeration for the final semantic claim

The first final-source battery correctly returned 11/12 because the declared schedule period had not been enumerated. I retained that failure and reran with `--enumerate-schedule-period --require-rotations-identifiable`. Only the latter receipt supports the 12/12 claim.

## D9 — Retain broad but finite lesson evidence

Three complementary checks were kept:

1. exact prior production recipe, proving the original failure is reversed on the same indices;
2. 960 cyclic rotations over 552 unique inputs, exhausting 60 starts per default/easy/medium/hard band for declared rivals;
3. 300 source-bound lessons with all 1,200 pair rotations and 1,200 unique inputs.

These are not population estimates and do not prove universal induction. Overlapping schedule windows are not statistically independent.

## D10 — Keep audit-only sources untouched

The assigned peer targets `021fb6acf24f` and `0994294912bf` were inspected and reproduced, but no source or notes under either target were edited. Their findings belong in `AUDIT.md` and retained evidence only.

## D11 — Final self-review

The repaired distribution still varies height, width, palette, side, alignment, line count, and marker placements; the new semantic witness is not tied to one fixed grid. Remaining limits are the finite special-row/reference-width domain, deterministic six-start curriculum, and the necessarily incomplete rival inventory.
