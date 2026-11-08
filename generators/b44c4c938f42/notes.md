# Current notes: b44c4c938f42

## Current rule and source

Generator version `3.2.0`, SHA-256 `33ce9d5349070343ba38e5386e00158382d482ba61f5e0683a71c276082f337a`.
Canonical rule `10339930cb51` is unchanged, with exact source SHA-256 `c28d990306ed0cc7d8a1c3bb6c9bbb0db4012f9c53124a7b0dc137eca66c4707`.

Split at all-zero columns, choose the unique largest same-color four-connected component in each panel, order selected objects by decreasing size, and greedily place them on one panel-width background-8 canvas using the canonical shift priority.

## Current repair decision

The prior generator's uniform distractor size made total colored panel area order-equivalent to selected-object size. That rival fits all six unique canonical pairs (12 stored labeled slots) and the entire old generated support. The exact strict inversion and actual Racket receipt are retained in `counterexamples/panel-total-area/`; `generated.json` is a final-source emitted counterexample independently labeled by the semantic gate.

Default standard-profile winners of sizes 3,4,5 now receive distractors of sizes 2,3,1, giving total areas 5,7,6. This strict inversion refutes the stronger total-area rival even when ties use selected size. Small-profile examples remain to teach size-2 winners. Explicit uniform distractor and two-panel overrides preserve their exact meanings. The new rival and its executable witness are declared in both semantic and lesson contracts.

Three-demo/one-query production lessons use four consecutive indexes. The alternating profiles preserve threshold and area-order evidence under any one-pair holdout. Final checks for this source:70 task tests pass;12 battery stages pass;300 lessons/1,200 query rotations show no ambiguity against the five declared rivals; all four start residues at seed0 across three bands pass12 lessons/48 rotations. Full reports are in the accompanying review return's `checks/` and `RESULTS.json`.

## Scope and remaining limits

The finite rotated-template family still uses monotonic panel rank order and no tied selected sizes. Endpoint-directed scanning and reversed tie behavior remain untested or unrefuted outside the five declared competitors; no universal induction or full shape-support claim is made. Explicit overrides can intentionally remove default teaching witnesses. Inherited handling of explicit `None` keys can also bypass default scheduling; default lesson guarantees require omitted overrides, not null placeholders. No canonical authority, approval or shared runtime was changed by this repair.

## Proposed extension

`workspace/parametric/` contains an unapproved two-setting horizontal-shift-preference prototype. Its default is byte-identical to the canonical program. A separate narrow vertical-overlap witness distribution distinguishes the two settings; six final episodes,24 pairs and24 rotations are Racket checked, with16 focused tests. The source-owned evidence manifest/proof retain the bindings and limits. This proposal does not change canonical production generation or imply training admission.

## Prior bounded audit disposition

The existing generated assessment below is preserved verbatim. It refers to earlier source bytes and does not describe fresh execution in this review.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-cd76f14ab38151f7:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `446650303b20d9648e28ff60f46949a090499d037275a1269b7d1a5e1b693653`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

One current decision covers both same-source findings: review-66f32fcc6493fdcb:v0001: Single-component and silently accepted unknown-control findings on baseline446650303b20 addressed by accepted0b202 return54a3f1e4f0bc: every panel has unique-largest plus same-color distractor, strict call contract,45 reported tests and300lesson/1200rotation checks. Reviewer-reported, not rerun; limited named-rival grammar. review-cd76f14ab38151f7:v0001: Original958single-component panels/support-collapse finding addressed by accepted0b202 return54a3f1e4f0bc with largest+same-color-distractor and alternating size2winner/distractor profiles;300lesson/1200rotation reported checks refute all-components/fixed-threshold rivals. Limited source-bound closure, no universal generalization claim.

### Assessment or prior finding

Source-bound supporting assessment from review-66f32fcc6493fdcb:v0001

## b44c4c938f42

**Reproduced teaching defect.** The generator creates exactly one connected non-8 component in each panel. Therefore the plausible rival “overlay every non-8 cell from each panel” is indistinguishable from the intended “choose only the largest non-8 component from each panel” on generated data.

I sampled 18 default inputs (6 each in easy, medium, and hard) from generator SHA `446650303b20d9648e28ff60f46949a090499d037275a1269b7d1a5e1b693653`. Every panel in every input had exactly one non-8 component. A Python rival that merges all non-8 panel cells and uses the canonical greedy shift order matched all 18 outputs obtained from the canonical Racket rule. The same rival disagreed with all 6 canonical pairs, which contain distractor components and demonstrate why “largest” matters. This is a generator-domain teaching gap, not a label mismatch. Evidence: `checks/audit/b44c4c938f42/analysis.json`, `input-batch.json`, and `racket.json`.

A separate contract defect is also reproduced: an unknown override key is silently accepted. The task lint fails for a missing rule pin and unprobeable axes; the override stage reports unknown-key acceptance and missing exact observation for five semantic axes. Evidence: `checks/audit-b44-lint/` and `checks/audit-b44-override/`.

No files for this audit target were modified.

Source-bound supporting assessment from review-cd76f14ab38151f7:v0001

## b44c4c938f42

**Reproduced distribution defect: the “largest component” decision is never
exercised.** The generator creates exactly one non-8 connected component in
each panel. A deterministic probe over 30 seeds × 4 sample indexes × all three
bands inspected 958 panels; the component-count histogram was `{1: 958}`.
Therefore the rival “take every non-8 component from each panel, then use the
same conflict-avoiding placement” is indistinguishable on the emitted stream.

The exact validator-accepted counterexample in
`checks/audit/b44c4c938f42/input.json` adds a small color-2 singleton to a panel
that also contains a larger color-1 component. The canonical Racket authority
omits the singleton, while the all-components rival retains it at output row 4,
column 4. `checks/audit/b44c4c938f42/racket.json` records generator SHA-256
`446650303b20d9648e28ff60f46949a090499d037275a1269b7d1a5e1b693653`,
executed rule hash `10339930cb51`, the exact input/output hashes, and a matching
catalog rule hash. The rival output and 958-panel probe count are in
`checks/audit/b44c4c938f42/rival.json` and
`checks/audit-b44c4c938f42.json`.

Suggested repair: generate at least two separated non-8 components in selected
panels, vary which is largest, and include examples where the smaller component
would remain visible under an all-components overlay. I did not modify this
audit-only target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-cd76f14ab38151f7-v0001/audit_assets.json), manifest SHA-256 `94427b05955d4073f0e09c5ddd11813b00a8abbf7b63f5b26af81865c5240498`.
<!-- arcpuzzles-current-audit-assessment:end -->

Exact authored parametric retention metadata is preserved as `workspace/parametric/evidence/prototype-manifest.json`; `proof.json`, code, and episodes are unchanged. The adjacent owner manifest inventories retained files. Neither tests nor prototype reads the old retention-index path; refresh the owner inventory after rerunning the separate retention-index authoring helper. Default schedule/null-placeholder limits are bound in `evidence/default-schedule-limits/manifest.json`.
## Current reviewer considerations

Source SHA-256: `33ce9d5349070343ba38e5386e00158382d482ba61f5e0683a71c276082f337a`.

# Decisions for b44c4c938f42

Canonical generator version: `3.2.0`.
Final generator SHA-256: `33ce9d5349070343ba38e5386e00158382d482ba61f5e0683a71c276082f337a`.
Baseline version/source: `3.1.0` / `54a3f1e4f0bca72832465acf6050aa5776977ec4128ccf255a3cbb6dad1fccbc`.

## D1 — Repair a surviving ordering shortcut

The baseline battery passed all 12 stages, but an independent rival search found that ordering by total colored panel area fits every canonical label and every old emitted input. Uniform distractor size makes that statistic order-equivalent to the selected component's size. Fresh Racket evaluation of a strict inversion demonstrates a real semantic difference. Evidence: `checks/canonical-review/confirmation.json`, `racket.json`, `census.json` and `FINDING.md`.

The repair changes only the default standard teaching profile: winners 3/4/5 get distractors 2/3/1. This is a strict inversion, so a total-area rival cannot evade it with a selected-size tie breaker. A mere equal-total example was rejected as insufficient against that stronger rival. The small profile remains available to teach size-2 winners, while the mixed standard profile retains a size-2 distractor and also teaches the selected-size ordering.

The canonical Racket program, selected target programs, canonical examples, shared runtime, catalog and audit-target generators are unchanged. No authority rewrite is needed for a generator support defect.

## D2 — Preserve exact controls; state the lesson scope

Explicit `distractor_size=1` and `2` still mean uniform distractors of exactly that size. An explicit two-panel request stays two panels. The new mixed default therefore omits `distractor_size` from observable overrides when no single uniform value exists. Default standard draws use three panels so the profile keeps all three useful object/distractor relationships. The override matrix and regressions check this distinction. An independent review also reproduced an inherited edge case: explicit `None` values are accepted by the shared context as absent controls, but the generator retains those keys before default scheduling. Consequently `distractor_size=None` or `panel_count=None` can remove a default witness. This return does not normalize that existing behavior; the lesson guarantee requires omitted overrides, and exact integer controls remain covered. See `checks/canonical-code-review.json`.

The production lesson policy is three demonstrations followed by one query, using four consecutive sample indexes. The declared phase schedule has period four. Every one-pair holdout preserves both alternating profiles and at least one strict area inversion. Final schedule enumeration covers all four start residues, all three bands and every query position at seed 0. The larger final census covers 100 lessons per band with query rotations. Neither result is an exhaustive statement about every seed or every override-defined lesson policy.

The new regression first failed against the baseline (five failures, four passes). After the sampling repair it passed nine tests. The first strict after battery then correctly rejected the incomplete semantic declaration: the canonical-fitting shortcut needed both a `SEMANTIC_RIVALS` entry and an executable `WITNESS_RIVALS` claim. A further test failed before that metadata fix (one failure, eight passes). The final nine-test run passes. All these genuine failures remain under `checks/panel-area-*` and `checks/after/`; they are intermediate evidence, not outstanding final failures.

## D3 — Keep the repair narrow and expose remaining restrictions

The generator still uses a finite set of rotated templates, two or three panels, and monotonically ordered selected sizes. It does not teach arbitrary rank permutations or equal-size stability. The independent old-source search also found an endpoint-directed scan and a reversed-tie rule that survive this restricted family. The three-panel area inversion closes the reproduced total-area shortcut; it does not close those distinct gaps.

Shuffling all panels and introducing tied winners would require additional placement templates, validator/override decisions and lesson evidence. That broader rewrite is deferred rather than silently folded into this repair. The declared grammar has five executable competitors: select all components, omit shifts, sort by total panel area, keep absolute size greater than one, and keep absolute size greater than two. Claims are restricted to that grammar and the measured sampling policies.

## D4 — Proposed parametric extension: horizontal shift preference

Status: **runnable prototype / proposed, not approved for training admission**. The implementation and README are in `repo/generators/b44c4c938f42/workspace/parametric/`, with 16 focused tests and a compact retained evidence manifest beside the source.

One meaningful rule parameter selects `left_first` or `right_first` horizontal shift preference. The parameter is drawn once per episode and remains fixed for its three demonstrations and one query. `left_first` preserves the exact canonical program bytes, SHA-256 `c28d990306ed0cc7d8a1c3bb6c9bbb0db4012f9c53124a7b0dc137eca66c4707`. `right_first` changes only horizontal signs in the canonical shift sequence; its program SHA-256 is `58995312aa58a57859df4f37be9ba9b78d354d6c160f096a9cb617f993612d26`, normalized rule hash `b7afb2eb5ef7`.

An initial attempt to use the canonical generator's existing templates exhausted the bounded 64-attempt search without identifying the parameter. That real failure is retained. The prototype consequently uses a separate, narrower witness distribution: nested vertical winners at a common column, smaller same-color distractors, and shuffled panel rank order, while retaining selected-generator dimensions, palette and panel count. It requires both programs to preserve all selected pixels and every accepted pair to distinguish the two settings. Exhausting the bounded search raises an error rather than emitting an ambiguous episode.

Fresh Racket execution checks six episodes, two settings across three bands, 24 pairs, six production lessons and 24 query rotations, plus the 12 canonical labeled slots for the unchanged default program and an explicit separating witness. Public challenge files omit parameters, program text and query answers. Private evidence records bindings and labels. See `checks/parametric/final-evidence/manifest.json`, `tests-final.json`, and the README for exact commands, limitations and intermediate failures. This is a deliberately small proof of the extension, not a broad distribution certification.

## D5 — Recover from extraction limits without changing the packet

The initial full extraction encountered actual ENOSPC. Only our incomplete extraction and later our own caches were removed; the original ZIP remained intact. A single persisted draw seed was used to derive and restore the necessary runtime closures, then the stock assignment machinery recorded the same draw. Audit targets were likewise drawn once. There was no reroll and no search for an easier task.

The source archive was fully streamed against its manifest: 88,091 manifest/entry files and 1,283,007,068 payload bytes, excluding the raw manifest itself. This is archive integrity verification, not physical full-tree verification. Our extracted work uses selected runtime closures. The evidence states `full_tree_verified: false` throughout.

Two optional standard-library tools are included under `checks/tooling/`. The extractor verifies paths, hashes, metadata and no-overwrite/rollback behavior. The archive-backed return adapter supplies only absent untouched repository files to the exact stock builder, imports stock tooling from verified ZIP bytes, and requires selected sources, baseline files, canonical source and evidence to remain physical. Present unauthorized edits cannot be hidden by fallback. It preserves all stock gates and lets stock code generate INTAKE. Its bounded version support and sparse-absence limitation are documented. Thirty-six tests pass, including byte-identical returns from synthetic full and sparse workspaces and independent stock validation. These are optional shared-tool proposals, outside the canonical source patch.

## D6 — Honest solves, audits and handoff

The blind solve was completed before inspecting task rules or generators, with earlier exposure and reference consultation both declared `no`. It matched all three visible examples; hidden query correctness is unknown. The later solve uses the final repaired source and declares earlier rule exposure `yes`. Work notes summarize actual experiments; they do not claim captured token-level reasoning or invented failures.

Both drawn audit sources remain unchanged. Findings distinguish fresh Racket labels from Python censuses and rule-domain counterfactuals from emitted support. The final handoff applies the exact returned patch in a fresh runtime-closure extraction, checks every changed-file hash, and runs focused tests in that checkout's own environment. Exact receipts and any limitations are recorded in `RESULTS.json` and `checks/final-replay/`.
