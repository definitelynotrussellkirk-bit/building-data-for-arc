# Working notes: fe947dc3e12c

## Current selected design (v5.0.0)

The intended rule is unchanged: find exactly three non-background 4-connected monochromatic components, sort by descending **cell count**, and recolor ranks `1`, `4`, `2`. The selected rule hash remains `0ef10b0042c4`.

Baseline v4.0.0 used mostly bars, so bounding-box area fit all five canonical pairs and 872/900 sampled ordinary outputs. A retained lesson had demos 162–164 all compatible with that rival and query 165 differing by 11 cells. Lead evidence came from prior return `review-ce35ccec4404bbb0:v0001` (asset manifest SHA `aa8c5f0a125b5edf4760f998bda1637cca745f67980d94ff1ec8528387daac54`).

The repair alternates two lawful textures:

- `bars`: component sizes and bbox areas agree;
- `bbox_witness`: sizes `(6,5,3)`, bbox areas `(6,8,4)`.

With three demos, one query, and period 2, every cyclic query rotation retains at least one witness demo. The exact axes are `grid_h=9..14`, `grid_w=9..16`, `palette_mode=canonical|varied`, and `texture=bars|bbox_witness`. Unknown controls and non-exact scalar types are rejected. Every fourth default slot is 10×10; other dimensions vary by difficulty.

`self_check` accepts only rectangular declared-size grids containing exactly three separated monochromatic nonzero 4-components with strictly distinct sizes and one of the canonical family size profiles. Ordinary generation currently uses only `(6,5,3)`; broader profile/topology variation remains open distribution work.

Final generator SHA-256: `dc857939405616b3cf68087979383c4150a7e7bc7e7f111b76db5f37b9766586`. Final battery: 12/12 green. Portable focused tests: 86/86 passed. Random lesson census: 300 lessons and 1,200 rotations with zero ambiguity/errors. Declared-period census: all six starts and 24 rotations passed.

The Racket semantics were not changed. Only `racket_target.target_code` formatting was synchronized; archival `raw_code` remains preserved.

A separate proposed-not-selected prototype parameterizes rank order as largest-first versus smallest-first. It is under `workspace/parametric/`; both two-setting episodes have live Racket/Python parity and distinguishing demonstrations.

Known limits: finite rival set, one generated size profile, finite witness topology bank, canonical palette as the ordinary default. No training admission is implied by the checks.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-dea6121d1126d10d:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `dc857939405616b3cf68087979383c4150a7e7bc7e7f111b76db5f37b9766586`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/fe947dc3e12c/generator.py,unchanged SHA256 dc857939405616b3cf68087979383c4150a7e7bc7e7f111b76db5f37b9766586. Bounded no_issue:86/86 reported task tests;initial semantic stage failed only declared_period_not_enumerated. Explicit fixed-seed0 follow-up covers both period2 starts inthree bands:6lessons/24rotations,plus12smoke lessons/48rotations and600draw semantic census clean. Canonical-fitting bbox_area_rank rival refuted bycell_count_not_bbox_area. Separate follow-up does not retroactively turn the initial combined preset into a pass. Finite seeds anddeclared hypotheses only. No owner audit execution,target source change ornew approval. Exact target-local citations: `checks/audit/fe947dc3e12c-combined/RUNTIME_MANIFEST.json` `checks/audit/fe947dc3e12c-combined/checks/fe947dc3e12c_audit_battery_summary.json` `checks/audit/fe947dc3e12c-combined/checks/fe947dc3e12c_audit_commands.jsonl` `checks/audit/fe947dc3e12c-combined/checks/fe947dc3e12c_audit_semantic_gate.json` `checks/audit/fe947dc3e12c-combined/checks/fe947dc3e12c_audit_semantic_gate.log` `checks/audit/fe947dc3e12c-combined/checks/fe947dc3e12c_audit_semantic_gate.receipt` `checks/audit/fe947dc3e12c-combined/checks/fe947dc3e12c_audit_summary.json` `checks/audit/fe947dc3e12c-combined/checks/task_tests.xml` `checks/audit/fe947dc3e12c-combined/progress.log` `checks/audit/fe947dc3e12c-combined/result.json` `checks/audit/fe947dc3e12c-semantic-enumerated/RUNTIME_MANIFEST.json` `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_battery_summary.json` `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_commands.jsonl` `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_semantic_gate.json` `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_semantic_gate.log` `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_semantic_gate.ok` `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_semantic_gate.receipt` `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_semantic_gate.schedule-census.json` `checks/audit/fe947dc3e12c-semantic-enumerated/progress.log` `checks/audit/fe947dc3e12c-semantic-enumerated/result.json`

### Assessment or prior finding

## fe947dc3e12c

### Verdict: No issue found after checking

The exact assigned generator SHA was `dc857939405616b3cf68087979383c4150a7e7bc7e7f111b76db5f37b9766586`; no source changed during audit. The combined preset executed 86 task tests with 86 passes. Its semantic stage initially returned a workflow warning—not a teaching counterexample—because the declared period 2 had not been enumerated. All sampled semantic evidence was otherwise clean: 12/12 lessons identifiable, 48/48 diagnostic rotations clean, and the canonical-fitting `bbox_area_rank` shortcut refuted by `cell_count_not_bbox_area`.

I ran the requested fixed-seed follow-up with required rotations and declared-period enumeration. It passed: 6/6 schedule lessons (both starts in all three bands), 24/24 period rotations, 12/12 smoke lessons, and 48/48 smoke rotations, with no ambiguity, hook warnings, or scoring errors. Evidence: `checks/audit/fe947dc3e12c-combined/checks/fe947dc3e12c_audit_summary.json` and `checks/audit/fe947dc3e12c-semantic-enumerated/checks/fe947dc3e12c_audit_semantic_gate.json`.

Scope limitation: this establishes the declared period at seed 0 plus the shared 600-draw semantic census; it does not prove every seed or every undeclared hypothesis. Within the assigned checks, I found no reproducible defect.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `dc857939405616b3cf68087979383c4150a7e7bc7e7f111b76db5f37b9766586`.

# Decisions: fe947dc3e12c

## D1 — Preserve the canonical cell-count rule

**Choice.** Keep the canonical rule unchanged: rank three non-background 4-connected objects by descending cell count and recolor them `1/4/2`.

**Rationale.** All five canonical pairs and the selected Racket authority support that rule. The prior review `review-ce35ccec4404bbb0:v0001` supplied a concrete lead, not a replacement rule: its audited generator SHA matches the assigned baseline, and its retained probe showed that bounding-box area was a shortcut because canonical objects were bars.

**Alternatives rejected.** Ranking by bounding-box area was rejected because it changes a lawful nonrectangular query by 11 cells. Changing connectivity, rank colors, or tie policy would alter the original reasoning pattern without evidence.

**Probe.** `checks/counterexample-final/` applies the live canonical Racket rule and compares it with the Python mirror and bbox-area rival.

**Limit.** Only three strictly different sizes are supported; equal-size tie semantics remain outside this generator's domain.

## D2 — Use a two-slot bar/witness schedule

**Choice.** Alternate `bars` and `bbox_witness` with `LESSON_SCHEDULE_PERIOD=2`, `EXAMPLES_NEEDED=3`, and one query.

**Rationale.** Any four consecutive samples contain two witness slots. Holding out any one pair leaves at least one witness among the three demos, so the bbox-area rival cannot fit the complete displayed support and then change the query.

**Alternatives rejected.** Randomly sprinkling witnesses was cheaper to code but could create unteachable short lessons. A four-slot schedule with only one witness could fail under query rotation. Making every scene a witness would weaken canonical-shape coverage unnecessarily.

**Probes.** The strict semantic gate checks 12 lessons and 48 rotations; `lesson-census-period` exhausts all six band/start combinations at seed 0; `self-review.json` independently checks 24 rotations.

**Failure mode.** This schedule only targets declared and bounded searched rivals. A different shortcut may require a new witness class.

## D3 — Make the input contract strict and observable

**Choice.** Expose exactly `grid_h`, `grid_w`, `palette_mode`, and `texture`; reject unknown keys and non-exact scalar types. Remove all advertised degenerate textures.

**Rationale.** The baseline silently ignored `bogus=123` and `size_1=9`, accepted weak scalar forms, and advertised behavior that did not belong to the intended three-object task. Exact controls are useful only when `observe_overrides` can recover them and the validator accepts every generated result.

**Alternatives rejected.** Keeping aliases for undocumented controls would preserve accidental API surface and make override testing misleading. Treating malformed values as defaults would hide upstream data bugs.

**Probe.** The final override matrix exercised all 127 legal combinations over 3 bands and 30 seeds each (11,430 calls) and explicitly checked unknown-key rejection.

**Limit.** The finite Cartesian matrix does not prove every future axis interaction; new axes require new tests and incompatibility declarations.

## D4 — Vary dimensions by difficulty while retaining canonical anchors

**Choice.** Reserve every fourth sample for 10×10, and draw other dimensions from difficulty-aware ranges.

**Rationale.** The linter correctly identified that the initial repair still overconcentrated defaults at 10×10 and did not make difficulty observable. Canonical anchors support exact-profile coverage; the remaining slots exercise the declared size envelope and difficulty control.

**Alternatives rejected.** Uniform full-range dimensions for every band would erase difficulty semantics. Removing anchors risked profile-floor failure and underrepresented the canonical layout.

**Probe.** Focused dimension tests were written before the implementation; final profile floor is 17/60 exact hits with nonzero support in every band.

**Limit.** Difficulty changes canvas size, not object count or rule complexity.

## D5 — Keep ordinary object sizes fixed at `(6,5,3)`

**Choice.** Generate one size profile while accepting all three canonical profiles in `self_check`.

**Rationale.** `(6,5,3)` supports a compact, placement-robust witness whose bbox areas are `(6,8,4)`. Varying sizes was not needed to repair the measured shortcut and would multiply topology/placement cases.

**Alternatives considered.** Cycling all three canonical profiles could improve coverage, but each would need a validated witness topology and full schedule/override replay. That was deferred rather than approximated.

**Probe.** `checks/self-review.json` explicitly reports the observed size-profile distribution.

**Limit.** This is the largest remaining task-local distribution restriction.

## D6 — Keep the rank-order parameter as a separate prototype

**Choice.** Implement `rank_order={largest_first,smallest_first}` under `workspace/parametric/`, with `largest_first` as the canonical default, but do not select it for production.

**Rationale.** It is a small parameter that preserves object extraction, size comparison, rank recoloring, and shape preservation. Separate prototype status prevents experimental variants from silently changing the selected task.

**Alternatives rejected.** Parameterizing output colors would change mostly surface form. Parameterizing measurement (cell count versus bbox area) would elevate a known wrong shortcut into an accepted variant. Parameterizing object count would no longer preserve the original three-rank mapping without extra semantics.

**Probe.** Two live Racket sources, two episodes, four labelled pairs per episode, Python parity, and cross-setting demo distinction are retained in `checks/parametric-final/`.

**Limit.** Only two settings and deterministic fixtures were tested; no variant training approval is claimed.

## D7 — Synchronize selected Racket formatting, not semantics

**Choice.** Reformat only `racket_target.target_code`; leave archival `raw_code` unchanged.

**Rationale.** The final authority checker expects the selected executable field to be synchronized. The rule itself and normalized hash were already correct. The automatic proposal tool rejected the source because duplicate target encodings made its text selection non-unique, so a narrow JSON-field edit was safer than a broad replacement.

**Alternatives rejected.** Rewriting both selected and archival fields would destroy provenance. Editing the canonical ledger was unnecessary and outside the evidence.

**Probe.** Final authority-sync and rule-smoke stages are green; `RULE_HASH` remains `0ef10b0042c4`.

## D8 — Leave peer-audit targets unchanged

**Choice.** Report, but do not patch, `69b886e1df03` and `a16cf9241d71`.

**Rationale.** The assignment asks for adversarial audits only. Both findings are source-hash-bound and independently Racket-labelled in `checks/audit/`.

**Failure modes and limits.** The `69b886e1df03` combined audit also had a portable task-test preflight failure, so its focused exact-control reproducer is the actionable evidence. The `a16cf9241d71` rival is a measured distribution shortcut, not proof of a model error or universal ambiguity.
