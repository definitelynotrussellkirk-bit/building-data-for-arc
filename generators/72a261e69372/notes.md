# Working notes: 72a261e69372

## Review scope

Assignment `review-0fba1e52e45bae75` reviewed the selected `2.0.1` baseline and repaired only task-local generator, tests, notes, and workspace files. No prior return or associated review note was present for this task, so none was used as a lead. The selected canonical Racket rule was not changed.

## Baseline findings

The baseline generated only clean disjoint/nested complete frames, but the canonical test contains a decisive occlusion: one color's apparent rectangle is interrupted by a later frame. The canonical rule recognizes only intact same-color connected rectangular outlines, so the marker associated with the broken color remains 1. Baseline `self_check` rejected that lawful canonical input, and the generator never taught the distinction.

Additional measured issues were an unpinned rule hash, no executable semantic witnesses/rivals, exact-looking axes that did not honor overrides, acceptance of unknown overrides, and no canonical-profile support in the pinned profile-floor check. The completed before battery (`checks/before/`) reported 6 green, 1 advisory, and 5 failed stages.

## Repair decisions

1. **Preserve the rule; repair the distribution.** The canonical rule passed smoke and authority checks. The defect was missing teaching support, not wrong Racket semantics.
2. **Teach two independent decisions.** Nested scenes refute “choose the outermost frame”; overlap scenes refute “a color bounding box is a frame even after overwrite.”
3. **Model occlusion structurally.** An occluded role is accepted only when its observed cells are a strict subset of its bounding-box perimeter and every missing perimeter cell is occupied by an intact frame color. A random hole is rejected.
4. **Give every role evidence.** Every intact frame is selected by at least one marker. Every occluded frame has an orphan marker enclosed by no intact frame.
5. **Make lesson support executable.** Four consecutive demonstrations must include both nested and overlap scenes and must cause every declared rival to disagree with at least one oracle output.
6. **Use exact, observable controls.** `grid_h=11..18`, `grid_w=13..20`, `n_frames=2..3`, `layout_kind=nested|overlap`, and `palette_kind=low|high|mixed` round-trip through `observe_overrides`. Unknown, wrong-type, and out-of-range values raise `ValueError`.
7. **Keep canonical scale without collapsing diversity.** Four of every five default samples use one of the three canonical `(height,width,color-count)` anchors; the fifth samples the full declared size/frame domain. Orientation remains a keyed dihedral draw.

## Test-first record

The baseline failed 24 new task-local regressions (`checks/task-tests-red.log`), including canonical acceptance, override honesty, semantic counterexamples, and robustness checks. The later lesson-level hook test also failed first because the contract did not yet exist (`checks/lesson-hook-red.log`). The final protected task-test run passes 47 tests with real Racket parity (`checks/task-tests-final-2/`).

## Final measured evidence

- Generator SHA-256: `9c4b036b290524b61b2eecd93a3ae62d28813148d8f396acdd61cb1e4faf8af7`.
- Completed final battery: 12/12 green, zero advisory/failure (`checks/after-final/`).
- Independent source-bound census (`checks/72a261e69372-independent-audit-final.json`): 600/600 distinct generated inputs, 0 self-check errors, 0 nondeterminism, 600 changed outputs, 489 canonical-profile hits, 296 bbox-rival disagreements, 304 outermost-rival disagreements, and 99/99 selected cases matching the real Racket rule.
- Actual lesson census: 200 lesson seeds per band, four demonstrations plus query; all 600/600 lessons were identifiable, included both layouts, and eliminated both declared rivals. Unique demo inputs were 800 easy, 797 medium, and 800 hard.

## Limitations

The generator intentionally focuses on the two decisive canonical ambiguities rather than every imaginable arrangement of rectangles. Its Python oracle is independently implemented but remains supplementary; selected cases were checked against Racket, not an exhaustive proof over the full combinatorial domain. The archival authority bank still contains an older divergent copy, while the selected authority is synchronized and execution parity passes; this is unchanged repository history, not a task-local rule modification.
## Current reviewer considerations

Source SHA-256: `9c4b036b290524b61b2eecd93a3ae62d28813148d8f396acdd61cb1e4faf8af7`.

# Decisions: 72a261e69372

## D1 — Repair the generator, not the selected rule

**Choice.** Preserve canonical rule hash `d763a0664108` and redesign the input distribution.

**Rationale.** Baseline rule smoke and authority synchronization were already green, and direct canonical comparison showed that the rule's exact-frame behavior explained every pair. The mismatch was that the generator omitted and rejected the canonical occlusion.

**Alternatives rejected.** Changing Racket to treat any color bounding box as a frame would make the canonical test wrong. Weakening validation without generating occlusions would accept the pair but still fail to teach it.

**Probe.** Before battery and canonical regression tests; final real-Racket parity in `checks/task-tests-handoff/` and `checks/72a261e69372-independent-audit-final.json`.

**Limitation.** The selected authority has an older archival divergent copy elsewhere in the repository; it remains unchanged and unselected.

## D2 — Define a frame as one exact same-color connected outline

**Choice.** Detect non-marker colors by 4-connected components and accept a component as a frame only when it equals the complete perimeter of its bounding box with a nonempty interior.

**Rationale.** This is the smallest operational definition that distinguishes the canonical intact frames from an overwritten apparent frame.

**Alternatives rejected.** Per-color global bounding boxes merge disconnected pieces and make the canonical occluded color look falsely complete. Merely checking corners or row/column extents admits broken outlines.

**Probe.** Canonical acceptance; mutation tests that erase one perimeter cell; dihedral-equivariance tests; independent oracle comparisons.

**Failure mode / limitation.** Multiple same-color exact frames remain detectable as separate components, but the selected generator intentionally uses distinct colors per role.

## D3 — Use paired nested and overlap scene families

**Choice.** Generate `nested` and `overlap` layouts as equal-frequency default families.

**Rationale.** Nested scenes isolate smallest-versus-outermost selection. Overlap scenes isolate exact-outline-versus-bounding-box recognition. One family cannot teach both decisions economically.

**Alternatives rejected.** Disjoint frames do not test containment choice. Only nested frames permit the bounding-box shortcut. Arbitrary occlusion placement created hard-to-validate accidental components and marker scarcity.

**Probe.** `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, final 600-draw census, and task tests with explicit rival disagreement.

**Limitation.** Geometry is template-based; arbitrary rectangle arrangements are not exhaustively sampled.

## D4 — Give every semantic role a marker

**Choice.** Place one marker for every intact frame's uniquely smallest region and one orphan marker for every occluded role.

**Rationale.** Every drawn color must affect at least one output decision. Otherwise decorative frames can support shortcuts or waste demonstration capacity.

**Alternatives rejected.** Random marker placement frequently left a frame unused or placed all markers in the innermost region. A single marker per scene underdetermined some multi-frame examples.

**Probe.** Structural `self_check`, destructive marker tests, changed-output count 600/600.

**Failure mode / limitation.** Markers are placed only in legal background cells, so extremely tight arbitrary layouts are outside the generated domain.

## D5 — Treat occlusion as overwritten perimeter, not damage

**Choice.** A broken role must be a strict subset of its own expected perimeter, and each missing edge cell must currently contain another intact frame color.

**Rationale.** This accepts the canonical visual cause of breakage while rejecting arbitrary holes that would make the intended latent rectangle unknowable.

**Alternatives rejected.** Accepting any perimeter subset would admit noise and ambiguous intended boxes. Requiring connected remnants would unnecessarily reject lawful cuts that split an outline.

**Probe.** Canonical test acceptance and `test_validator_rejects_unexplained_hole_in_occluded_outline`.

**Failure mode / limitation.** The validator assumes overwriting by another colored role, not erasure to background.

## D6 — Expose five exact controls only

**Choice.** Advertise and validate `grid_h`, `grid_w`, `n_frames`, `layout_kind`, and `palette_kind`; reject every unknown control.

**Rationale.** Each axis has an unambiguous observable decoder and materially changes the grid. Fewer honest controls are better than broad metadata with dead aliases.

**Alternatives rejected.** Retaining inherited `density`, `texture`, or generic palette-size controls would add names without independent behavior. Silent fallback on invalid values hides curriculum bugs.

**Probe.** Round-trip tests in every band, wrong-type/range tests, final override gate.

**Failure mode / limitation.** Orientation is intentionally an internal keyed draw rather than an override axis.

## D7 — Use two or three frames

**Choice.** `n_frames=2..3`.

**Rationale.** Two frames are the minimum for both decisive comparisons; three add an intermediate tier without forcing much larger grids.

**Alternatives rejected.** One frame cannot distinguish smallest from outermost. Four or more frames compressed marker regions and reduced canonical-scale support.

**Probe.** Exact override tests, profile floor, all-marker-role validation.

**Failure mode / limitation.** Deeper nesting is not represented.

## D8 — Anchor most defaults to canonical scale, retain a broad slot

**Choice.** Use the three canonical `(height, width, color-count)` profiles in four of every five samples, with one full-domain sample per five-position schedule.

**Rationale.** The baseline failed the canonical profile-floor gate. Purely broad random sampling rarely landed exact profiles; a 100% fixed schedule would collapse size diversity.

**Alternatives rejected.** Difficulty-only size bands missed exact canonical combinations. Always forcing canonical dimensions would make the generator too narrow.

**Probe.** Final profile floor: 51/60 exact hits and support in every band; independent census: 489/600 hits while every declared dimension value appeared.

**Failure mode / limitation.** Difficulty mostly changes anchor weighting rather than semantic complexity; both rule branches remain present in every band.

## D9 — Use three fixed palette families with distinct colors

**Choice.** `low=(2,3,4)`, `high=(7,8,9)`, and `mixed=(2,6,9)`.

**Rationale.** These span low, high, and separated color values while avoiding background 0 and marker 1. Distinct colors keep component roles observable.

**Alternatives rejected.** Arbitrary sampling adds no rule complexity and complicates override observation. Same-color nested frames merge into one component and change the task.

**Probe.** Palette round-trip tests and diversity census.

**Failure mode / limitation.** The exact palette triplets are limited; color permutation generalization is sampled across three families rather than all combinations.

## D10 — Apply keyed dihedral presentation variation

**Choice.** Reflect vertically/horizontally through a four-value internal orientation draw; tests also check all eight dihedral transforms.

**Rationale.** It breaks fixed-side positional cues without changing rectangular containment semantics or grid dimensions.

**Alternatives rejected.** Arbitrary 90-degree rotation swaps requested height/width and makes exact override observation ambiguous. No transform leaves overlap direction as a shortcut.

**Probe.** Determinism/hash-seed test and eight-transform equivariance test.

**Failure mode / limitation.** The production draw uses reflections, while test coverage establishes that the rule/validator also tolerate transposed rotations.

## D11 — Make complete lessons identifiable, not merely the pooled corpus

**Choice.** Alternate default layout by sample-index parity and implement `lesson_identifiable` for four demos plus query.

**Rationale.** Witness frequency across 600 unrelated draws does not guarantee that one exported lesson refutes every rival. Consecutive four-demo lessons now necessarily contain both families.

**Alternatives rejected.** Pure random layout selection has a nonzero chance of all-nested or all-overlap lessons. A post-hoc retry loop would obscure the actual trainer schedule.

**Probe.** Red lesson-hook test, final semantic smoke (12 lessons), and independent 200 lessons per band; 600/600 passed with zero rival survivors.

**Failure mode / limitation.** The guarantee assumes the documented consecutive sample-index assembly policy. A different exporter that skips indices should call the hook and reject/reassemble failures.

## D12 — Add an independent oracle and bounded census

**Choice.** Build `workspace/reference_probe.py` without importing generator-private rule-mirror helpers.

**Rationale.** Tests that call the same implementation twice can agree on the same bug. The probe independently reconstructs components, exact frames, outputs, profiles, and shortcut behavior, then samples real Racket.

**Alternatives rejected.** Racket on every thousands-of-case census would be slower; Python-only evidence would not establish selected-authority parity.

**Probe.** Final report: 600 draws, 600 actual lessons, and 99 real-Racket comparisons.

**Failure mode / limitation.** It is still finite sampled evidence; it explicitly does not claim universal induction.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-8292552d8414577e:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `9c4b036b290524b61b2eecd93a3ae62d28813148d8f396acdd61cb1e4faf8af7`. At disposition, audited bytes match the current source.

### Current decision

The retained audit explicitly reported no issue in its bounded source-bound scope. Preserve that limitation; no universal correctness or new owner execution is inferred.

### Assessment or prior finding

## 72a261e69372

**No issue found.** I ran the task's independent source-bound probe against
generator SHA-256
`9c4b036b290524b61b2eecd93a3ae62d28813148d8f396acdd61cb1e4faf8af7`
and rule hash `d763a0664108`. It reproduced all 3 canonical outputs, generated
120 deterministic lawful cases (40 per difficulty band), and observed 56
occluded-frame cases plus 64 nested-smallest-frame cases. The bbox-as-frame
rival disagreed on all 56 occlusion witnesses and the outermost-frame rival
disagreed on all 64 nested witnesses. All 120 four-demonstration lesson windows
were identifiable, with both layout kinds present and neither rival surviving.
A 99-grid balanced sample also matched the selected Racket authority with zero
mismatches. Evidence: `checks/audit/72a261e69372/reference-probe.json`; command
output: `checks/audit/72a261e69372/reference-probe-console.log`.

Scope limit: this is finite sampling, not a universal proof. I specifically
checked the prior high-risk areas: treating an occluded outline as intact,
choosing the outermost rather than smallest exact frame, missing layout support,
and lesson-level rival survival.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-8292552d8414577e-v0001/audit_assets.json), manifest SHA-256 `275e7f7667a021cdfeeed821a53f5ec06258374a15a542ff345bba9ad0a867ab`.
<!-- arcpuzzles-current-audit-assessment:end -->
