# Working notes: ebe355c22d70

## Current design

Version 3.0.0 generates exactly two blue opposite-corner markers on a zero background. The inclusive bbox is 3..6 on each axis, both slants are ordinary, and the unchanged Racket authority returns a newly cropped solid-8 rectangle of the bbox dimensions. `RULE_HASH` is pinned to `cd9402783d01`.

The honest controls are `grid_h`, `grid_w`, `bbox_h`, `bbox_w`, and `slant`. All are exact and observable. Unknown, malformed, out-of-range, and incompatible controls are rejected. The prior version's palette/texture/count/aspect aliases were removed because they were constant, dead, overlapping, or outside the lawful grammar.

## Reversed decisions

- **Prior choice:** ordinary placement always increased both row and column, so every generated pair had positive slant. **New choice:** a deterministic four-phase schedule includes both slants. **Reason:** retained review `review-e5ff77276ca08f17:v0001` measured 900/900 positive generated pairs while 2/3 canonical pairs are negative.
- **Prior choice:** describe/fill the rectangle on the original canvas. **New choice:** document and teach a cropped output. **Reason:** all three canonical pairs and the selected authority return only the solid bbox.
- **Prior choice:** broad nominal axes including textures and degenerate controls. **New choice:** five strict lawful axes. **Reason:** override diagnostics showed dead controls and unknown-key acceptance.
- **Intermediate choice:** four scheduled output shapes under a declared sixteen-shape codomain. **New choice:** one slot for every 3..6 × 3..6 bbox. **Reason:** the linter and focused codomain test exposed the mismatch.
- **Intermediate choice:** use `[]` as a rival sentinel. **New choice:** every executable rival returns a valid grid. **Reason:** the first large census produced 300 production and 1,200 rotation scoring errors.

## Teaching policy

The sixteen-slot cyclic schedule begins with the three exact canonical linked profiles and then covers the remaining bbox sizes. Any four consecutive pairs leave three demonstrations containing both slants and a nonsquare bbox after any query rotation. Eight executable rivals cover orientation-only, same-size fill, border-only fill, row/column squares, fixed 5×5, and identity shortcuts.

Focused tests enumerate all sixteen starts in all three bands. The reusable `workspace/probe_schedule.py` also enumerates all query rotations and uses the live rival declarations. The final 300-lesson Racket census found no ambiguity against those rivals, but this is finite-hypothesis evidence, not a proof against every possible rule.

## Known limits and open findings

Each bbox size occupies one scheduled slant, so size and slant are not fully crossed. Slant does not affect the authoritative output and no declared query-changing rival survives, but a future 32-slot schedule could balance both slants for every size. Catalog approval and training admission remain external decisions. No Racket authority file was changed.
## Current reviewer considerations

Source SHA-256: `fb03a8ef6351a4a592ecb21b048bff10fbd7f14ab4193eeca5defb0185f846a4`.

# Decisions for `ebe355c22d70`

## D1 — Use the retained audit as a lead, then remeasure the pinned baseline

I consulted only the relevant prior return indexed as `review-e5ff77276ca08f17:v0001`. It identified an orientation gap against source SHA-256 `490e5aadd6435ecc5880a64e9a365a67403595403d676419c99c5458e3d6a2e5`, which exactly matched this assignment's baseline. I treated the prior report as a hypothesis, not as current-source proof, and reproduced the associated lint/override defects before changing code. The retained source-bound witness is under the selected task's existing `counterexamples/` tree.

## D2 — Keep the Racket rule unchanged and correct the generator contract

The visible canonical pairs and the selected Racket authority agree on a simple operation: take the inclusive bounding box of the two blue cells and return a newly cropped solid-8 grid. The defects were in sampling, metadata, validation, and lesson construction, not in the authority. I therefore pinned `RULE_HASH = "cd9402783d01"` and left every authority file byte-for-byte unchanged.

Rejected alternative: changing the rule to produce a filled rectangle on the original canvas. That would make the stale baseline summary true but would contradict all three canonical outputs and the selected authority.

## D3 — Replace dead aliases with five exact, observable axes

The final axes are `grid_h`, `grid_w`, `bbox_h`, `bbox_w`, and `slant`. Each affects the returned grid, is reported by `observe_overrides`, has a narrow documented range, and is exercised in every difficulty band. Unknown keys, wrong types, out-of-range values, and impossible bbox/grid combinations are rejected instead of silently ignored.

Rejected alternative: retain `palette_kind`, `texture`, `palette_size`, `num_corners`, `position_bias`, `n_distinct_colors`, and `bbox_aspect` as nominal controls. Most were constants, aliases, or out-of-domain degenerates; keeping them would make override coverage look richer without adding lawful data.

## D4 — Bound the ordinary bbox grammar to 3..6 on each axis

The canonical output dimensions are 5×5, 6×5, and 6×6. The 3..6 range preserves all linked profiles while adding smaller square and rectangular outputs. It creates a finite sixteen-member output codomain that can be exhaustively covered and audited. Input grids remain 6..14 on each axis so every bbox fits with varied placement.

Rejected alternative: use the full input-grid range for bbox sizes. That increases nominal diversity but makes exact codomain coverage and compact lessons more difficult without adding a distinct reasoning operation. The present range can be widened later if model evidence shows saturation.

The official linter exposed an intermediate mistake: the first repair declared sixteen possible output rectangles but generated only four. `checks/task-tests-codomain-red.log` preserves that failure. I added exact `bbox_h`/`bbox_w` controls and a complete sixteen-profile schedule rather than lowering the declaration to match the incomplete implementation.

## D5 — Use a deterministic sixteen-slot teaching schedule

The first three slots reproduce the three canonical linked profiles. The remaining thirteen slots complete the sixteen 3..6 × 3..6 bbox combinations. A repeating `positive, negative, negative, positive` slant phase plus nonsquare odd slots guarantees that every four consecutive labelled pairs leaves an identifying three-demo set after any query rotation.

Alternatives considered:

- Pure random sampling: broader incidental variation, but no guarantee that a three-demo lesson contains both orientations or a nonsquare output.
- Hand-picked fixed lessons: teachable but poor coverage and difficult to audit across starts.
- A 32-slot schedule with both slants for every bbox size: better marginal balance, but unnecessary for the current output rule and twice the period. This remains a reasonable future extension.

The schedule is cyclic in `seed + sample_index`. Tests and `workspace/probe_schedule.py` enumerate every one of the sixteen possible starts in each difficulty band rather than sampling a few starts.

## D6 — Declare executable query-changing rivals

The eight declared rivals are orientation-only, same-canvas fill, border-only crop, row-span square, column-span square, fixed 5×5 output, and identity. They were chosen because each produces a different query answer on lawful inputs and captures a plausible interpretation of the visible transformation.

A first implementation used `[]` to mean “the orientation-only rival declines this branch.” That was invalid: executable rivals must always return a rectangular ARC grid. The 300-lesson census surfaced 300 production and 1,200 rotation scoring errors. The repair uses a valid deliberately wrong 1×1 solid-8 grid and adds a focused test that validates every rival output. This red-to-green evidence is in `checks/lesson-census.json`, `checks/task-tests-rival-grid-red.log`, and `checks/lesson-census-v2.json`.

## D7 — Treat arbitrary query rotation as supported, then test it exhaustively

The production lesson order is deterministic, but there is no semantic reason the fourth pair must always be the query. I therefore designed the schedule so any pair can be withheld. The successful census uses rotation policy `require`; the custom probe checks all cyclic starts and all four query positions. This is stronger than the battery's small smoke test but remains limited to the declared rivals.

## D8 — Preserve canonical anchors while adding broad profiles

`strict_canonical_like` recognizes the exact three canonical linked profiles. They occupy 3/16 of each complete schedule, above the declared 0.15 strict-profile floor. The rest of the schedule broadens bbox shape, placement, input size, and orientation without changing colors or the reasoning operation.

Rejected alternative: synthesize “canonical-like” profiles by matching only one coordinate such as output size. Exact linked profiles are easier to audit and avoid claiming support for combinations never present in the source examples.

## D9 — Validate actual pixels, not only requested controls

The new analyzer rejects empty, ragged, wrong-sized, noninteger, out-of-palette, wrong-count, aligned, and out-of-range-bbox inputs. All semantic hooks derive from this analyzer. This prevents malformed handcrafted inputs from being accepted merely because generator metadata looked valid.

## D10 — Keep the source-bound failures and segmented battery history

The before battery was interrupted with a known lint failure and is reported only as partial. Final-source battery execution also exposed a wrapper-lifecycle issue: completed child stages were checkpointed, but the outer process remained alive. I used the documented `--resume` flow without changing source or settings; the final aggregate binds all twelve green receipts to generator SHA-256 `fb03a8…`. I did not merge the incomplete and complete aggregates or describe the partial run as a pass.

## D11 — Solve records remain separate from generator evidence

The blind task `c1b540a1d7b0` was completed before opening task-specific sources. Its first minimum-cover hypothesis failed one visible example; revision 2 added a nonoverlap tie-break and matched all three. The later `ebe355c22d70` solve was explicitly exposed (`earlier_rule_exposure: yes`) and matched 3/3 visible examples on revision 1 without consulting a reference during the solve. Neither record claims hidden-query correctness.

## Limitations

- The rival set is finite and reviewer-authored; passing it does not prove the lesson rules out every alternative hypothesis.
- The schedule intentionally correlates each bbox size with one scheduled slant. Because slant is irrelevant to the output and both slants are common, no tested query-changing shortcut results, but a 32-slot balanced schedule would remove this artifact.
- Catalog approval and train-safety admission remain outside this review.
- The two audit findings are evidence against other generators only; those sources were not modified.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ec52e63fbf31a209:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `fb03a8ef6351a4a592ecb21b048bff10fbd7f14ab4193eeca5defb0185f846a4`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported on unchanged source fb03a8ef6351a4a592ecb21b048bff10fbd7f14ab4193eeca5defb0185f846a4. No issue within the finite declared schedule/rival scope: combined audit passes 33 tests and strict semantics. The task-local probe covers 16 profiles, 48 cyclic starts across three bands, 192 rotations and 1536 checks against eight rivals; codomain size is 16 and there are zero violations. No claim is made for undeclared rules or inputs outside the domain. Retain source-bound evidence: `checks/audit/ebe355c22d70-combined-command.log` `checks/audit/ebe355c22d70-combined/RUNTIME_MANIFEST.json` `checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_battery_summary.json` `checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_commands.jsonl` `checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_semantic_gate.json` `checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_semantic_gate.log` `checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_semantic_gate.ok` `checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_semantic_gate.receipt` `checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_summary.json` `checks/audit/ebe355c22d70-combined/checks/task_tests.xml` `checks/audit/ebe355c22d70-combined/progress.log` `checks/audit/ebe355c22d70-combined/result.json` `checks/audit/ebe355c22d70-schedule-probe.json` `checks/audit/ebe355c22d70-schedule-probe.log`

### Assessment or prior finding

## ebe355c22d70

**Conclusion: No issue found** within the declared finite schedule and rival
scope. Audited source SHA:
`fb03a8ef6351a4a592ecb21b048bff10fbd7f14ab4193eeca5defb0185f846a4`.
No source was changed.

The combined portable audit passed 33/33 task tests and the strict semantic gate:
`checks/audit/ebe355c22d70-combined/checks/ebe355c22d70_audit_summary.json`.
I also ran a task-local exhaustive schedule probe over:

- all 16 declared schedule profiles;
- 3 bands × 16 cyclic starts = 48 starts;
- 4 query positions per start = 192 rotations;
- 8 declared rivals = 1,536 rival-rotation checks.

The observed output codomain was 16, matching the declared codomain; all 16
profiles appeared, and there were zero violations. Evidence:
`checks/audit/ebe355c22d70-schedule-probe.json`.

**Limit.** This establishes consistency only for the declared deterministic
16-profile schedule and the eight declared rivals. It does not prove
identifiability against every possible rule or input outside the documented
domain.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## Parametric extension review-fc240b35715369e2 (2026-10-24)

- Preserve the exact canonical outer-bounding-box solid-8 program byte-for-byte as `mode=outer_fill`.
- Add `mode=short_side_relay`: derive the outer nonzero bounding box, use its shorter side as an input-dependent cell-count selector, crop the unique matching non-blue component, and render its exact normalized mask in color 8.
- Use matched inputs across settings, 2–6 demonstrations, four distinct private queries, and a 30×30 fourth query. Two demonstrations refute the alternate setting and nine authored finite shortcuts; this is bounded evidence, not a universal uniqueness proof.
- Retain an executable long-side counterfactual so qualification can show the final answer changes when the intermediate is wrong.
- A 50-seed all-count stress sweep exposed a greedy placement dead end at seed 8. The repair preserves the preferred distractor shape when placeable, then tries other connected snake aspect ratios deterministically. The repaired sweep covers 500 episodes and 4,000 visible pairs with zero failures.
- Owner acceptance and training admission remain pending; reviewer evidence establishes only readiness for those gates.
