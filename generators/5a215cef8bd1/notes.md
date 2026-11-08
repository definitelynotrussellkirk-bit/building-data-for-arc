# Working notes: 5a215cef8bd1

## 2026-10-03 review-f89bda355e4fdac7

Baseline generator v3.1.0 completed the 12-stage battery with 7 green, 2 advisory, and 3 failed stages. Blocking issues were missing rule binding, false/dead axis declarations, ignored exact overrides, accepted unknown overrides, and defect-lint findings. Profile support and semantic teaching were advisory.

The decisive semantic defect was geometric: the selected Racket rule allocates output slots from the original template height and width. Clockwise rotation swaps rectangular dimensions, so old generated rectangular templates could occupy the central separator/neighboring slot or clip while still producing a valid grid. The authority was not changed. Generator v4.0.0 restricts generated and validated template bboxes to square sizes 2–4, adds four relative layout modes, exact observable axes, strict structural validation, deterministic canonical-profile anchors, and a 3/2/4 size schedule.

All four canonical pairs use 3×3 templates, so `fixed_3x3_panel` is a genuine canonical-fitting rival. It is now declared under the semantic contracts and refuted by a non-3×3 witness in every three-demonstration schedule window.

Final evidence:

- generator SHA-256 `49bc35a0a7bbd175ccca39ef864dd46f874d7d0f09f42030c8280ab9b60b8776`;
- after battery 12/12 green;
- portable task tests 108/108 passed with Racket available;
- production lesson census 300/300 identifiable, 1,200/1,200 unique inputs;
- independent probe 750 samples, 0 validation/determinism/cell-loss failures, 28/28 Racket parity;
- selected Racket authority unchanged, hash `b5c73de1606e`.

Deliberate limitation: generated templates distinguish all four transforms. Canonical-like symmetric shapes remain valid under `self_check` but are not sampled in v4.0.0; a future lesson-aware sampler could mix them while retaining an asymmetric witness elsewhere in the lesson.

See `workspace/reference_probe.py`, task tests, `REVIEW.md`, and `DECISIONS.md` for reproducible details. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `49bc35a0a7bbd175ccca39ef864dd46f874d7d0f09f42030c8280ab9b60b8776`.

# Decisions for 5a215cef8bd1

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical Racket program unchanged and pin it with `RULE_HASH = "b5c73de1606e"`.

**Rationale.** The rule is internally consistent on square template bounding boxes, matches all four canonical pairs, and passed real-Racket execution. The observed corruption came from the generator admitting shapes the fixed slot geometry cannot safely contain, not from disagreement among canonical examples.

**Alternative considered.** Change the Racket output slots to `max(th, tw)` or shape-specific dimensions. Rejected because that changes established output dimensions and canonical semantics merely to accommodate unsupported generated inputs.

**Probe/evidence.** `workspace/reference_probe.py::rectangular_counterexample`, the rectangular regression test, 4/4 canonical oracle matches, and 28/28 Python–Racket parity checks.

**Limitation.** The lawful generated domain is narrower than a hypothetical revised rule that explicitly supported rectangular templates.

## D2 — Restrict generated template bounding boxes to square sizes 2, 3, and 4

**Choice.** Enumerate connected square-bbox polyomino families at sizes 2/3/4, with counts chosen to retain many shapes and all four bounding-box sides occupied.

**Original rationale.** The imported v3.1.0 summary described bboxes 2–4 in each dimension, but no retained evidence justified rectangular support. The selected rule allocates slots from the original dimensions.

**Alternatives considered.** (a) Keep only 3×3, which preserves canonical shape but teaches the fixed-7×7 shortcut; (b) use rectangular shapes and reject only those whose particular rotation crosses a slot; for a 90° transform, any non-square bounding box changes dimensions, so this is fragile and complicates semantics without adding a new concept.

**Failure modes checked.** Separator pollution, clipping, disconnected templates, missing bbox sides, invalid sizes, and lost transformed cells.

**Limitation.** Shape families deliberately distinguish all four transforms. Symmetric lawful examples are accepted by validation but not sampled.

## D3 — Make transform identity observable in every generated example

**Choice.** Sample only shapes whose identity, clockwise rotation, 180° rotation, and left-right reflection have four distinct normalized signatures.

**Rationale.** A control-to-transform mapping is not learnable from an example if two requested transforms happen to be visually identical. Per-example observability makes lesson construction robust and keeps the generated evidence easy to audit.

**Alternative considered.** Mix symmetric and asymmetric examples with a lesson-level constraint. This would better cover canonical-like symmetry, but it requires the sampler to enforce cross-example support for every transform equivalence class. That is a reasonable future extension, not needed for the current repair.

**Probe/evidence.** Task tests enumerate sampled transform signatures; generated families are checked before use. Canonical symmetric inputs remain accepted.

## D4 — Replace decorative axes with five exact controls

**Choice.** Declare only `grid_h`, `grid_w`, `template_size`, `control_order`, and `layout_mode`.

**Rationale.** These are visible in the input, independently observable, and materially affect a lesson. The old palette/texture/position aliases were not honest controls and caused tens of thousands of override mismatches.

**Alternatives considered.** Keep aliases for backward compatibility. Rejected because they advertised behavior the generator did not honor and allowed invalid degenerates into exact-control tests.

**Failure modes checked.** Every minimum/maximum axis value, all 24 order indices, all four layouts, invalid types/ranges, unknown keys, deterministic replay, and observer agreement.

**Limitation.** No palette axis is exposed because task colors are semantic constants, not style choices.

## D5 — Support four relative layout modes

**Choice.** Place controls above, below, left, or right of the template, with overlap on the perpendicular axis and at least one blank row/column on the separating axis.

**Rationale.** The rule depends only on control row/column rank, not an absolute “template on top, controls below” convention. Varying this relation prevents a position shortcut while preserving unambiguous object separation.

**Alternative considered.** Allow fully diagonal placement. Rejected for now because a diagonal scene can satisfy two layout labels, making exact override observation ambiguous. The selected placements have one designated separating axis.

**Probe/evidence.** All four modes were observed in both task tests and the 750-sample probe (186/183/195/186).

## D6 — Use a 12-profile deterministic schedule with 3/2/4 template sizes

**Choice.** `schedule_profile = sample_index mod 12`; template sizes repeat `3,2,4`; residues 0/3/6/9 anchor the four canonical canvas dimensions.

**Rationale.** The production lesson sampler uses three demonstrations. Every three consecutive samples therefore contain a non-3×3 witness, while one-third remain canonical-sized templates. Anchors make canonical canvas support deterministic rather than accidental.

**Alternatives considered.** Pure random size sampling could yield all-3×3 lessons. A strict 2/4-only schedule would refute the shortcut but underrepresent the canonical form. A larger stateful lesson-aware scheduler was unnecessary.

**Probe/evidence.** The census tested 100 lessons per band and all six start residues; all 300 lessons refuted the fixed-3×3 rival.

**Limitation.** The finite schedule explicitly targets the strongest observed canonical-fitting shortcut; it does not prove all possible rival programs are excluded.

## D7 — Make `self_check` structural, canonical-tolerant, and override-aware

**Choice.** Validate grid shape/range/palette, exactly one connected color-2 object, square bbox 2..4, exact singleton controls, the complete 2×2 control rectangle, and separation. Compare requested override metadata to observed values when supplied.

**Rationale.** The previous checker mostly counted colors and let geometry errors through. The new checker protects the executable assumptions that determine labels.

**Alternative considered.** Require transform asymmetry in `self_check`. Rejected because canonical inputs can be symmetric and remain valid; asymmetry is a generation policy, not a universal task law.

**Probe/evidence.** 60/60 generated inputs clean, 4/4 canonical accepted, and 50/50 destructive mutations rejected.

**Limitation.** The checker does not execute the Racket program. Runtime parity is covered separately.

## D8 — Add an executable canonical-fitting rival

**Choice.** Implement `fixed_3x3_panel`, declare it in all semantic-rival interfaces, and expose `non_3x3_template` as the witness.

**Rationale.** All canonical pairs have 3×3 templates and 7×7 outputs. This is therefore a real shortcut, not a synthetic wrong answer invented after seeing generated data.

**Alternative considered.** Declare only textual shortcut notes. Rejected because the semantic gate and census need executable disagreement on actual lesson queries.

**Probe/evidence.** Rival fits 4/4 canonical pairs, disagrees on 501/750 independent generated samples, and is refuted by 300/300 production lessons.

**Limitation.** Only declared rivals are measured; the result is not universal identifiability.

## D9 — Add both focused tests and a reusable independent probe

**Choice.** Put regression tests in the task's supported `tests/` directory and a standalone oracle/census in `workspace/reference_probe.py`.

**Rationale.** Tests catch contract regressions cheaply; the probe gives future reviewers a source-bound way to inspect distribution, determinism, geometry, canonical agreement, and optional Racket parity without relying on generator-internal output code.

**Alternatives considered.** Rely only on the full battery. Rejected because the battery did not originally expose the rectangular transform-footprint defect and does not discover task tests automatically.

**Failed iteration retained.** The first source-tree probe imported a module available only in prepared runtime. The portable version uses `reviewer_support.canonical_pairs` and reads the selected canonical row directly for Racket parity. The failure is retained in `checks/reference-probe.console.log`.

**Limitation.** The Python oracle mirrors the compact rule independently but is still reviewer-authored; authoritative labels remain the Racket outputs.
