# Current notes: 87aae821984d

## Intended rule

Count every yellow (`4`) cell. Treat every cyan (`8`) cell as one logical motif, even when the cyan cells are not 4-connected. Take the motif's tight bounding box, place it in a fixed 3×3 tile aligned to the tile's bottom-right (therefore padding a short motif on top and a narrow motif on the left), and repeat that tile horizontally once per yellow cell.

The selected Racket program is the output authority and is pinned by `RULE_HASH = "6f52927247b0"`. `rule_mirror()` is an independently implemented Python mirror used only for contracts and tests.

## Repair decisions

The previous `3.2.0` generator made two semantically incorrect assumptions: it required one connected cyan component, and its prose described tight-bounding-box tiling rather than fixed 3×3 bottom/right alignment. It also advertised controls and degenerate textures that were ignored, clamped, or outside the lawful task domain.

Version `4.0.0` reverses those choices:

- disconnected cyan motifs are legal and deliberately generated;
- the four observable bbox classes are explicit: `span_3x3`, `pad_top`, `pad_left`, and `pad_top_left`;
- the public override surface is reduced to four exact controls that are all observed after construction: `grid_h`, `grid_w`, `n_4_cells`, and `shape_kind`;
- unknown and wrong-type overrides fail rather than being silently ignored or clamped;
- generation uses constructive placement, so every declared joint override combination is realizable;
- a deterministic four-profile curriculum supplies three demonstrations plus one query and covers count, padding, horizontal alignment, and disconnected-motif evidence in every cyclic lesson window.

The canonical ledger's selected `program_solution` was changed only by removing whitespace/newlines. Its executable expression is unchanged; authority-sync and execution-parity checks pass.

## Strongest retained shortcut

All seven canonical cyan motifs span three columns. Consequently, this plausible rival fits every canonical pair: bottom-align the motif vertically, but left-align any motif narrower than three columns (pad on the right instead of the left).

The executable rival is `left_align_narrow_motif`. A minimal retained witness is `counterexamples/padding-fragmentation-count.json`: its cyan bbox is 3×2, so the intended tile begins with a zero column while the rival ends with a zero column. The generator emits such witnesses through the `pad_left` and `pad_top_left` profiles. The focused tests require the rival to fit all seven canonical pairs and disagree on the retained witness.

## Evidence

Final generator SHA-256: `15a3c012540738dee4d3d31f9ffe68b8eebfcdfda23836b0cc4c3be0fd9b99b8`.

- focused task tests: 38/38 pass (`checks/task-tests-final/result.json`);
- full source-bound battery: 12/12 stages green (`checks/after-final-rival/checks/87aae821984d_after_battery_summary.json`);
- strict-profile support: 25/60 exact canonical-profile draws, with support in every band (`checks/after-final-rival/checks/87aae821984d_after_profile_floor.json`);
- semantic census: 600/600 draws materialized without crashes, all witnesses fired in all bands, and 12/12 smoke lessons plus 48/48 query rotations were identifiable against the declared rivals (`checks/after-final-rival/checks/87aae821984d_after_semantic_gate.json`);
- large lesson census: 300/300 lessons and 1,200/1,200 held-out-query rotations had no ambiguity against the finite declared rival set (`checks/lesson-census-final.json`).

## Known limits

- The lesson checks cover a finite declared rival set; they are not a proof of unique induction against every possible rule.
- Output diversity is intrinsically smaller than input diversity because outputs are only a 3×3 motif repeated one to five times. The final diversity gate still passes; its 300-draw sample had 100% unique inputs and 39% unique outputs.
- Supported cyan motifs have 3–8 cells and tight bbox dimensions 2–3 by 2–3. Solid 3×3 motifs are excluded because they erase motif geometry.
- Difficulty mainly changes default canvas scale and schedule defaults. It is not a calibrated psychometric difficulty measure.
- Catalog approval and training admission remain unchanged by this review.
## Current reviewer considerations

Source SHA-256: `15a3c012540738dee4d3d31f9ffe68b8eebfcdfda23836b0cc4c3be0fd9b99b8`.

# Decisions for `87aae821984d`

Each decision records the prior choice, evidence, alternatives, and known failure mode. Finding IDs match `REVIEW.md`.

## D1 / R87-1 — Treat all cyan cells as one logical motif

- **Prior choice:** require exactly one 4-connected cyan component. The original rationale was documented as avoiding component ambiguity.
- **New choice:** accept all cyan cells inside one 2–3 by 2–3 tight bbox, regardless of connectivity.
- **Evidence:** two of seven canonical inputs are disconnected, and the selected Racket program uses `find-color` over all cyan cells rather than component selection. The old self-check therefore rejected valid authority examples.
- **Alternatives rejected:** (a) largest component only, which changes two canonical outputs; (b) connect fragmented examples with synthetic cyan cells, which changes the task; (c) exclude disconnected canonicals, which violates authority.
- **Probe:** canonical-pair tests plus rival `largest_connected_component_only`; retained schedule profile `span_fragmented_canonical` and `pad_left_fragmented`.
- **Failure mode/limit:** a cyan arrangement with bbox larger than 3×3 is outside this generator's declared domain even if the Racket expression can mechanically evaluate it.

## D2 / R87-1 — Fixed 3×3 tile with bottom/right alignment

- **Prior choice:** documentation said “crop the cyan bbox and tile it,” and generation mostly used full 3×3 bboxes, hiding the difference.
- **New choice:** reconstruct a fixed 3×3 window ending at the bbox's maximum row/column; short bboxes gain top padding and narrow bboxes gain left padding.
- **Evidence:** the selected program computes `pad-r = 3 - sh` and `pad-c = 3 - sw`. Canonical examples include a 2-row motif that distinguishes top padding from tight-bbox tiling.
- **Alternatives rejected:** top/left alignment, tight-bbox output, or arbitrary normalization. All disagree with authority on at least one canonical or retained witness.
- **Probe:** `rule_mirror`, the four shape classes, and `counterexamples/padding-fragmentation-count.json`.
- **Failure mode/limit:** all canonical motifs span three columns, so horizontal alignment required an added generated witness; it was not identifiable from canonicals alone.

## D3 / R87-2 — Narrow the public override contract

- **Prior choice:** advertise eight axes plus helpful and degenerate textures. Several were unused, aliases were not honored, integers were clamped, and degenerates failed `self_check`.
- **New choice:** expose only `grid_h`, `grid_w`, `n_4_cells`, and `shape_kind`, with exact types/ranges and no silent coercion.
- **Evidence:** baseline defect lint/override stages failed; final override checker reports 16,920 accepted draws and zero findings.
- **Alternatives rejected:** keep compatibility aliases (preserves ambiguity/dead controls); declare many incompatible combinations (unnecessary because construction can support the full Cartesian space); clamp invalid values (makes controls non-exact).
- **Probe:** focused boundary/type/unknown-key tests, `observe_overrides()`, and the shared Cartesian override checker.
- **Failure mode/limit:** callers relying on undocumented old aliases will receive explicit errors; this is intentional contract repair.

## D4 / R87-2 — Construct layouts instead of retrying random placement

- **Prior choice:** random shape growth plus bounded placement retries.
- **New choice:** enumerate legal motif origins, shuffle deterministically, and choose isolated yellow cells from a viable parity sublattice.
- **Evidence:** every legal joint override combination must be realizable, including five counters on a 9×9 canvas. Constructive search makes failure indicate a real contract error rather than unlucky retries.
- **Alternatives rejected:** increase retry limits (still probabilistic); use unconstrained rejection sampling (can hang or become seed-sensitive); silently enlarge the grid (would violate exact overrides).
- **Probe:** full Cartesian focused test and 16,920-draw shared override check.
- **Failure mode/limit:** construction is specialized to the small 9–14 canvas and 2–3 cell bbox ranges; larger general packing is not implemented.

## D5 / R87-3 — Use four semantic profiles, not a decorative shape bank

- **Prior choice:** random connected 3×3 shapes from named decorative kinds. This varied appearance but not the rule distinctions students needed.
- **New choice:** schedule bbox/alignment/connectivity classes: full fragmented, top-padded connected, left-padded fragmented, top-and-left-padded connected.
- **Evidence:** these four classes directly witness all authority-sensitive distinctions and remain easy to observe from a generated input.
- **Alternatives rejected:** purely random profile selection (can omit a needed witness from a lesson); keep seven named shapes (does not guarantee padding); add more profiles (no additional declared rival justified the complexity).
- **Probe:** `schedule_profile`, profile coverage in semantic gate, and all cyclic starts in focused tests/census.
- **Failure mode/limit:** motif density and exact geometry still vary randomly inside each class, but the schedule itself is intentionally predictable over four positions.

## D6 / R87-3 — Require three demonstrations and test every query rotation

- **Prior choice:** no explicit lesson contract.
- **New choice:** `EXAMPLES_NEEDED = 3`; production materializes three demos and one query from a period-4 schedule. `lesson_identifiable` requires every declared rival to be falsified by the demos.
- **Evidence:** any three of the four scheduled profiles contain enough evidence for the six declared rivals. Final census held out each of the four pairs in every materialized lesson: 1,200/1,200 rotations passed.
- **Alternatives rejected:** two demos (insufficient for all count/padding/connectivity combinations); four demos (unnecessary extra context); production-order-only testing (could hide a query-position dependency).
- **Probe:** 12-lesson semantic smoke, 300-lesson required-rotation census, focused exhaustive residue tests.
- **Failure mode/limit:** identifiability is only against declared deterministic rivals, not every imaginable hypothesis.

## D7 / R87-4 — Pin and synchronize the selected authority

- **Prior choice:** no `RULE_HASH`; canonical selected program had multiline formatting while the assignment selected the same expression in compact form.
- **New choice:** declare `RULE_HASH = 6f52927247b0` and compact only the selected canonical program's whitespace.
- **Evidence:** exact authority sync and Racket execution parity pass. The token/expression structure and all canonical outputs are unchanged.
- **Alternatives rejected:** change generator to an unpinned authority (not reproducible); change Racket semantics (not justified); suppress sync failure (would weaken provenance).
- **Probe:** authority-sync report, 120-case Racket smoke, Python mirror parity.
- **Failure mode/limit:** the canonical JSONL file hash changes despite semantic equivalence; this is disclosed in the maintainer brief.

## D8 / R87-3 — Make rivals and witnesses executable

- **Prior choice:** no semantic hooks.
- **New choice:** declare six rivals: top-left alignment, tight-bbox tiling, fixed one repeat, fixed three repeats, largest component only, and left-align narrow motifs. Pair them with five measurable witnesses.
- **Evidence:** every witness fires in every band; on 60 checked witness draws per claim, each declared rival disagreed with the authority every time.
- **Alternatives rejected:** prose-only checklist (not source-bound); infer rival names from tests (drifts from production); include weak cosmetic hypotheses that never change outputs (not useful).
- **Probe:** semantic gate and task-local regression suite.
- **Failure mode/limit:** future reviewers should add a new executable rival when they identify a stronger canonical-fitting shortcut rather than treating this list as complete.

## D9 / R87-5 — Retain the horizontal-padding canonical shortcut

- **Prior choice:** initially the repair covered top padding, tight-bbox, count, and connectivity rivals; it did not name the fact that canonicals never contain a narrow cyan bbox.
- **New choice:** add `left_align_narrow_motif` to `CANONICAL_SHORTCUTS`, semantic rivals, lesson competitors, and witness mapping.
- **Evidence:** it fits 7/7 canonical pairs exactly, but disagrees on the retained 3×2 input. The final census refutes it in all 300 production lessons and all 1,200 query rotations.
- **Alternatives rejected:** call it implausible because no canonical contradicts it (that is exactly why it is dangerous); add only a test without generated coverage (would not fix lessons); alter canonical examples (outside scope).
- **Probe:** canonical-fit test, retained JSON counterexample, `left_padded_shape` witness, final census.
- **Failure mode/limit:** the counterexample also refutes several weaker rivals, so tests separately assert the shortcut's 7/7 canonical fit to establish why it is the strongest one.

## D10 — Preserve canonical-sized support in every difficulty band

- **Prior choice:** difficulty-specific dimensions made hard-band canonical-size support vanish.
- **New choice:** schedule residues 0 and 1 use 9×9 canvases in every band; later residues scale by band.
- **Evidence:** final profile floor finds 11/20 easy, 9/20 medium, and 5/20 hard exact canonical-profile draws; all seven canonical inputs pass self-check.
- **Alternatives rejected:** make every draw 9×9 (unnecessarily restricts input variety); opt out of profile floor (hides distribution drift); rely on a single residue (the first trial was 14/60 overall and missed the required threshold).
- **Probe:** retained intermediate profile-floor failure and final source-bound profile report.
- **Failure mode/limit:** hard-band canonical support is lower than easy-band support by design, though nonzero and above the shared gate.

## D11 / A74-1 — Audit-only targets remain unchanged

The assigned audits were adversarial review, not repair authority. `74e83caa0660` has a reproduced inert `n_pairs` control; `486375757aca` had no issue found after the checks listed in `AUDIT.md`. Neither audited generator was edited.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/87aae821984d/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D9 — Native anchor family and source-bound tile witness (2026-10-25)

- Added `tile_anchor = bottom_right | top_left`; `bottom_right` preserves the accepted canonical program byte-for-byte.
- Inputs are setting-independent, support 2–6 demonstrations and four distinct queries, and include a populated 30×30 input / 3×30 output stress profile.
- The branch has a real motif-extraction → normalized-3×3-tile → repetition dependency. The official protected-Racket witness changes the anchor-produced intermediate and final repeated output.
- Bounded self-review covered 16 seeds × 2 settings × 5 demo counts = 160 episodes and 640 one-query public projections with no surviving declared rival. Native qualification passed four jobs and 32 protected-Racket evaluations.
- Regression retained for the valid exactly-two-counter case after the first sampler incorrectly attempted to place a third counter.
- Limitation: finite seeds and named rivals do not prove universal uniqueness; owner acceptance and training admission remain separate.
