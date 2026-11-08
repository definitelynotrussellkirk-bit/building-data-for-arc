# Working notes: 406739865b43

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `5af59a1154f8f278bdf0a43eff4ed9775bbc2eeddfd29df65f7aeec3c0a80554`.

# Decisions for `406739865b43`

Final generator SHA-256: `5af59a1154f8f278bdf0a43eff4ed9775bbc2eeddfd29df65f7aeec3c0a80554`.

## D1 — Keep the canonical rule unchanged

**Original rationale:** unknown beyond the task summary; the canonical examples and selected Racket authority consistently implement “row-0 color legend selects the matching body component, then tight-crop it.”

**Decision:** retain the rule and pin `RULE_HASH = c69934b21e7a`. Add a Python mirror only for tests and semantic probes.

**Alternatives considered:** rewrite the rule to match baseline quirks; broaden the rule to multiple matching components; remove the top-left tie-break. Those would change authority without evidence.

**Probe:** all four canonical pairs match the mirror; final rule-smoke is 120/120 with zero crashes; authority sync passes.

**Failure mode / limitation:** mirror agreement is sampled beyond the four canonicals, not a formal proof of all-grid equivalence.

## D2 — Replace the old axis surface instead of patching each decorative knob

**Original rationale:** inferred from source names only. The baseline exposed `grid_h`, `grid_w`, `n_decoys`, `n_distinct_colors`, `palette_kind`, `palette_size`, `position_bias`, `density`, and `texture`, but several were dead, inconsistent across bands, or not independently observable.

**Decision:** expose four exact semantic controls:

1. `scene_profile` — four canonical dimensions plus explicit `broad`;
2. `selection_profile` — `anchor`, `rank2`, `rank3`;
3. `target_cells` — exact 3..6;
4. `palette_profile` — `low`, `high`, `mixed`.

Unknown axes, wrong types, and out-of-range values fail closed.

**Alternatives considered:** retain compatibility aliases; declare dozens of incompatibilities; keep negative fixtures under `texture`. These preserve a misleading API and make exporter failures likely.

**Probe:** 8,910 override draws across 99 cases and three bands all accepted and round-tripped with zero findings.

**Failure mode / limitation:** callers depending on undocumented baseline axes must migrate; this is intentional because those axes were not trustworthy exact controls.

## D3 — Default to exact canonical dimension/palette profiles

**Original rationale:** baseline distribution appeared intended to be varied, but no written reason justified zero exact canonical hits.

**Decision:** cycle default dimensions through 10×10, 11×11, 12×12, and 12×13, always with background plus three nonzero colors. Keep noncanonical 10..14 dimensions behind the `broad` exact override.

**Alternatives considered:** probabilistic 8–25% canonical prior; envelope-only matching; an opt-out. A probability cannot guarantee per-band support in small exported samples.

**Probe:** final profile floor is 60/60 exact and 60/60 envelope, versus baseline 0/60 exact and 5/60 envelope.

**Failure mode / limitation:** defaults underrepresent very large grids; those were not canonical and added no task-specific teaching value.

## D4 — Use three/four separated components and a nonrectangular target

**Original rationale:** canonical examples contain separated monochrome objects and an irregular selected crop. Baseline random blobs allowed many nuisance combinations without a clear teaching purpose.

**Decision:** target is a connected nonrectangular 3–6-cell polyomino spanning at least two rows and columns. Decoys are connected 1–8-cell shapes placed in separated quadrants. Three-object anchors and four-object counterexamples use exactly three body colors.

**Alternatives considered:** arbitrary component counts, rectangles, repeated marker-color decoys, diagonal connectivity. These complicate the rule or permit easy shape/position shortcuts.

**Probe:** self-check and mutation fixtures reject missing/duplicate markers, occupied separators, multiple matching components, and extra palette colors.

**Failure mode / limitation:** the support is deliberately narrower than all lawful legend-selection scenes; future expansion should preserve semantic counterexamples and exact observability.

## D5 — Five-slot lesson schedule with four demonstrations

**Original rationale:** the packet declares `EXAMPLES_NEEDED = 4`; the canonical set leaves `farthest_from_marker` consistent with all four examples.

**Decision:** cycle `anchor, rank2, rank3, rank2, rank3`; export four consecutive demonstrations and the fifth pair as query. Every four-of-five rotation contains both rank-2 and rank-3 evidence.

**Alternatives considered:** pure random profiles; always-target-rank-2; three demonstrations; rejection sampling after lesson assembly. Random schedules can occasionally retain a middle-rank rival, fixed rank creates a shortcut, and rejection sampling hides coverage problems.

**Probe:** 300 production windows and 1,500 query rotations refute every declared competitor; no generation or scoring errors.

**Failure mode / limitation:** the cyclic proof covers the five-slot schedule and declared rivals, not arbitrary lesson lengths or undeclared rules.

## D6 — Align order, size, and marker-distance ranks

**Original rationale:** no baseline rationale existed. The goal is to make each rank profile easy to observe and test while alternating profiles across the lesson.

**Decision:** rank-2 scenes put the target at rank 2 by top-left order, size, and marker distance; rank-3 scenes put it at rank 3 for all three. Anchor scenes are rank 2 among three objects.

**Rejected first implementation:** it requested distance rank 3 for a top-right target and rank 2 for a bottom-left target. Fixed quadrants make those requests impossible. The retained failure in `checks/green-task-tests-1/` established the geometric root cause.

**Probe:** final rank probe reports only the three intended signatures, over 1,500 pairs.

**Failure mode / limitation:** correlating the three ranks makes each individual pair less factorially diverse. The lesson alternation refutes all fixed rank selectors; a future extension could independently permute ranks if it preserves guaranteed four-demo coverage.

## D7 — Palette roles vary, output colors are not fixed

**Original rationale:** canonical colors vary and the rule is color-role based, not numeric-color based.

**Decision:** sample three distinct low, high, or mixed colors; assign target and decoy roles randomly from that palette. Four-object scenes repeat one decoy color so the whole grid still has exactly four colors including background.

**Alternatives considered:** fixed canonical colors; arbitrary palette size; numeric-min/max target roles. These would teach color identity or rank shortcuts.

**Probe:** semantic rivals include smallest/largest, marker swatch, and position/distance selectors; all are refuted in every tested lesson window.

**Failure mode / limitation:** the probe does not enumerate every possible color-role heuristic. Numeric role permutations remain bounded to ARC colors 1..9.

## D8 — Difficulty changes nuisance draws, not the rule

**Original rationale:** baseline difficulty-specific ranges existed but were inconsistent with advertised exact domains.

**Decision:** keep the same semantic schedule and exact override domain in every band. Difficulty changes target-size weights and keyed nuisance draws (palette, shapes, placement), while exact overrides remain honored.

**Alternatives considered:** band-specific legality or semantic profiles. Those caused the baseline's declared/default rejections.

**Probe:** task tests require non-byte-identical bands; override audit checks all three bands under every exact case.

**Failure mode / limitation:** difficulty is not calibrated to model accuracy; it is a diversity stratifier.

## D9 — Declare only genuine canonical shortcuts

**Original rationale:** initial rewrite conservatively copied every semantic rival into `CANONICAL_SHORTCUTS`.

**Decision:** compute the canonical fit matrix in tests and declare only `farthest_from_marker`, the sole rival fitting all four canonical pairs.

**Alternatives considered:** leave all rivals declared or declare none. The former misstates evidence; the latter loses a real reason generated counterexamples are required.

**Probe:** test-first failure retained at `checks/red-canonical-shortcuts/`; final task test recomputes the fit matrix.

**Failure mode / limitation:** a new canonical corpus revision could change the ambiguous set; the test will fail loudly.

## D10 — Build a reusable, independent cyclic-start probe

**Original rationale:** the shared census samples production lessons but explicitly does not enumerate every cyclic schedule start or independently report component ranks.

**Decision:** add `workspace/selection_rank_probe.py`. It iterates actual `LESSON_COMPETITORS`, tests production and every query rotation, independently extracts order/size/distance ranks, verifies canonical shortcut declarations, records exact seeds and source hash, and emits JSON.

**Alternatives considered:** rely only on semantic-gate smoke tests or copy rival names into a one-off notebook. The former is too small; the latter silently drifts from the contract.

**Probe:** `checks/selection-rank-probe.json`, 300 starts, 1,500 pairs, 1,500 rotations, zero failures.

**Failure mode / limitation:** it uses the Python rule mirror for cheap scale; final Racket rule-smoke separately binds that mirror to authority.
