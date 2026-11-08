# Working notes: 72c77addd109

## Review-b669e671215aed9a repair

The selected 2.0.1 generator taught only filled rectangles, rejected lawful canonical arbitrary solids, advertised dead/overlapping axes, and did not pin the canonical rule hash. All four canonical pairs also left two plausible shortcuts alive: pair solids by reading order or by color rather than by cell-count rank.

Version 3.0.0 keeps the existing Racket authority unchanged and rebuilds the input curriculum around its actual domain:

- two arbitrary connected solids with unequal cell counts and two hollow frames with unequal interior areas;
- exact observable axes for dimensions, solid grammar, rank order, color order, frame order, and palette;
- canonical-size/palette anchors in every difficulty band;
- explicit irregular-shape and border-overwrite witnesses;
- executable Python mirror, named rivals, witnesses, and lesson-identifiability hook;
- a six-slot deterministic schedule whose every four-pair cyclic window still leaves all five declared rivals refuted after any one pair is used as the query.

Task-local tooling lives in `workspace/reference_probe.py` and `workspace/lesson_probe.py`. The latter checks the full endpoint-axis cross-product and cyclic query rotations that the shared source-bound census intentionally does not cover. Regression tests live in `tests/test_generator.py`; retained red/green evidence is in the review return's `checks/` directory.

Limits: finite declared-rival checks do not prove universal identifiability, and the Python rule mirror is corroborating test machinery rather than authority. The canonical Racket program remains the sole label authority.
## Current reviewer considerations

Source SHA-256: `2d77cdf1ca4a1374f1022c3acc7b2171f22a1736d4d6d2c2ffcb5ea102df0c86`.

# DECISIONS — 72c77addd109

These decisions apply to generator version `3.0.0`, SHA-256 `2d77cdf1ca4a1374f1022c3acc7b2171f22a1736d4d6d2c2ffcb5ea102df0c86`. The existing Racket program with rule hash `a657cfe83f60` remains authority.

## D1 — Preserve the Racket authority; repair the generator around it

**Decision.** Do not edit the canonical row or selected Racket solution. Pin `RULE_HASH = "a657cfe83f60"` and make the generator, validator, Python audit mirror, and lessons conform to that program.

**Rationale.** The before battery's `rule_smoke`, `racket_lint`, and `authority_sync` stages were green. The failures were generator-side: canonical-domain rejection, missing hash pin, dead axes, zero profile support, and weak/incorrect lesson controls. Changing an already-correct authority would have obscured the actual defect and increased review scope.

**Alternatives rejected.** I rejected narrowing or rewriting the Racket rule to “filled rectangles that fit inside interiors.” That would make the baseline generator easier to validate but would contradict canonical arbitrary solids and the authority's lawful border-overwrite behavior. I also rejected modifying canonical examples to fit the generator.

**Probes.** Before and after rule smoke plus authority sync; Python `rule_mirror` agreement on canonical pairs, generated samples, and the exact shortcut counterexample; supported `arcpuzzles apply` outputs in `checks/shortcut/72c77addd109/racket.json`.

**Failure mode/limit.** The Python mirror is not a second authority. Any future divergence must be resolved in favor of the selected Racket program and canonical examples.

## D2 — Treat “solid” as any lawful connected monochrome component, not a filled rectangle

**Decision.** Generate and validate two non-frame 4-connected monochrome objects with unequal cell counts. Support `rectangles`, `irregular`, and `mixed` styles. Preserve each object's exact tight-crop cells when rendering.

**Original rationale.** The baseline comments and summary asserted filled rectangles, but that rationale was incompatible with canonical train[0] and train[2]. No trustworthy retained evidence justified rectangle-only narrowing.

**Rationale for repair.** R1 was a direct domain mismatch: the baseline validator rejected two of four canonical inputs. The authority ranks non-frame components by cell count and pastes their tight crops; it does not require filled bounding boxes. Irregular examples are also necessary to refute the “fill the bounding box” shortcut.

**Alternatives rejected.** Merely loosening `self_check` while continuing to generate only rectangles would pass canonical validation but leave the curriculum unable to teach shape preservation. Random unrestricted walks were also rejected because they make dimensions and fit behavior difficult to control reproducibly. Small curated connected-shape banks plus dihedral transforms provide exact area, dimensions, irregularity, and deterministic coverage.

**Probes.** Canonical acceptance tests; style-override observation; destructive mutation tests; `fill_solid_bounding_box` rival and `irregular_solids` witness; 66/100 irregular-shape witnesses in each sampled default band.

**Failure mode/limit.** The irregular bank is finite. It establishes nonrectangular and holed-bounding-box behavior, not arbitrary polyomino coverage.

## D3 — Fit crops to the frame's outer bounding box, not necessarily its interior

**Decision.** Require each rank-paired solid crop to fit within the paired frame's outer rectangle. Center relative to the interior exactly as the authority does, then paste nonzero solid cells after drawing the frame without clipping.

**Rationale.** Canonical and authority behavior permit a crop larger than a one-cell interior dimension, so paste cells can overwrite border pixels. The baseline “must fit inside frame interior” invariant was too narrow and silently removed a meaningful semantic branch.

**Alternatives rejected.** Interior-only fit and clipping were rejected because they disagree with authority. Allowing crops larger than the outer frame was rejected because that could write outside the frame bbox and eventually outside the canvas.

**Probes.** `clip_to_frame_interior` rival, `border_overwrite` witness, Racket parity, and 95/97/96 border-overwrite witnesses among 100 easy/medium/hard defaults in `checks/task-probe-final.json`.

**Failure mode/limit.** The generated frame/shape banks make border overwrite frequent, perhaps more frequent than canonical examples. This is intentional teaching support, not an estimate of natural prevalence.

## D4 — Replace legacy metadata axes with seven exact, observable controls

**Decision.** Public axes are `grid_h`, `grid_w`, `solid_style`, `solid_rank_order`, `frame_rank_order`, `solid_color_order`, and `palette_kind`. Unknown keys and invalid type/domain values are rejected before generation. Every public exact axis is recoverable by `observe_overrides` from the returned grid.

**Rationale.** The baseline's `palette_size`, `n_distinct_colors`, `density`, and `position_bias` were singleton or non-probed declarations; `texture` overlapped palette and degenerate behavior. They created the appearance of combinatorial control without observable variation. The replacement axes map directly to geometry or palette and to identified semantic risks.

**Alternatives rejected.** I rejected retaining singleton axes as diagnostics because callers could still mistake them for exact controls. I also rejected a generic `texture` alias because it conflates palette, object grammar, and degenerate cases. No degenerate override is needed for the core teaching distribution.

**Probes.** Strict override unit tests, unknown-key rejection, independent `observed()` oracle, declared `observe_overrides`, battery override gate, and the full 576-case endpoint cross-product: 2 heights × 2 widths × 3 styles × 2 solid orders × 2 frame orders × 2 color orders × 2 palettes × 3 bands.

**Failure mode/limit.** Exact observation depends on deliberately placing each pair on a shared row and using left-to-right order. Future layout generalization must either preserve observability or revise the public contract.

## D5 — Use canonical dimension/palette anchors while preserving wider variation

**Decision.** In a six-slot schedule, slots 0 and 3 use 11×12 and slots 1 and 4 use 11×13. Other slots use wider difficulty-aware dimensions. Canonical palettes occupy two of each three semantic slots; the third is varied.

**Rationale.** The baseline produced zero of 60 canonical-profile hits even though canonical inputs are 11×12 or 11×13 with role palettes `{2,5}` and `{7,8}`. Anchors satisfy strict profile support and keep generated lessons near public examples, while non-anchor slots retain width/height and palette variety.

**Alternatives rejected.** All-canonical dimensions/palettes would reduce diversity and make color-role shortcuts more tempting. Pure random dimensions could again miss canonical profiles in small battery samples. A per-band single fixed size would create band-identifying artifacts and weak override coverage.

**Probes.** Final profile-floor gate; task-local defaults showing 67/100 strict canonical-like samples per band; 300 unique default inputs across the task-local probe; source-bound census unique-input counts.

**Failure mode/limit.** The periodic anchor schedule is deterministic and therefore discoverable if `sample_index` leaks. In normal lessons, model-visible data contains grids, not schedule indices.

## D6 — Deliberately cross size rank with reading order and color order

**Decision.** Encode solid and frame rank order geometrically through left-to-right placement. Two of every three semantic slots use descending reading order relative to area rank; two of three also reverse solid color order. Declare reading-order and color-order rivals explicitly.

**Rationale.** Both wrong solid-pairing rules fit all four canonical pairs. A curriculum that merely randomizes positions/colors without checking semantic disagreement could still fail to refute them. The exact counterexample at seed 117, sample 4 reverses both solid reading and color order, and its Racket result differs from both rivals in 11 cells.

**Alternatives rejected.** One counterexample every four lessons was initially considered sufficient at the individual-example level, but the cyclic query regression showed it was not lesson-safe. Fully random order was rejected because finite lesson windows can accidentally contain no counterexample.

**Probes.** Canonical-fit assertions (4/4 for both rivals), saved Racket counterexample, witness counts, shared lesson census, and cyclic query rotation probe.

**Failure mode/limit.** The schedule makes order counterexamples frequent (66/100 sampled defaults). That is a teaching choice, not a claim about canonical prevalence.

## D7 — Design lesson windows, not just individual examples

**Decision.** Use a three-slot semantic period with order settings `ascending, descending, descending`. The six-slot dimension schedule is compatible with this period. Test every four-pair start and every choice of one query, requiring the remaining three demonstrations to refute every named rival.

**Rationale.** R4 showed why per-example witness frequency is insufficient. The first implementation passed the shared 300-lesson census, yet when the only descending example was moved to the query position, `solid_reading_order` remained consistent with all visible demonstrations. Two descending slots in every three ensure any three consecutive demonstrations contain a rank-order counterexample.

**Alternatives rejected.** Adding a fourth demonstration would change the normal lesson budget. Forcing the query always to a harmless schedule position would make materialization brittle and hide the problem. The chosen schedule fixes identifiability without increasing lesson size.

**Probes.** Retained failing cyclic test (`checks/cyclic-red.log`), passing repair (`checks/cyclic-green.log`), 36-test suite, and 360 task-local cyclic checks.

**Failure mode/limit.** The cyclic proof covers the deterministic six-slot production schedule and five declared rivals. It does not cover arbitrary resampling policies or undeclared hypotheses.

## D8 — Separate validation, strict-profile measurement, and semantic teaching

**Decision.** Keep three distinct contracts:

- `self_check`: broad lawful-domain validation;
- `strict_canonical_like`: canonical-size/palette profile measurement;
- `lesson_identifiable`: outputs must match the mirror and visible demos must refute every named competitor.

**Rationale.** Combining these concerns caused the baseline to reject lawful canonical inputs and could tempt future fixes to narrow generation merely to satisfy a profile metric. Separate hooks make it clear that “lawful,” “canonical-like,” and “teaches the intended distinction” are different properties.

**Alternatives rejected.** A single strict validator was rejected because canonical profile is not the full task domain. Relying only on battery heuristics was rejected because it would not express task-specific rival hypotheses.

**Probes.** Canonical validation, mutation suite, profile-floor battery, semantic gate, shared census, and task-local probe.

**Failure mode/limit.** `lesson_identifiable` uses the Python mirror; authority parity must continue to be checked separately with Racket.

## D9 — Add reusable task-local tooling rather than modifying shared tools in-task

**Decision.** Add `workspace/reference_probe.py` and `workspace/lesson_probe.py`, plus focused tests in `tests/test_generator.py`. Do not patch shared census or linter code from this selected-task return.

**Rationale.** The assignment permits only selected-task changes. The shared lesson census already provides source-bound Racket scoring and materialized lessons, but explicitly omits cyclic query rotations and full joint axis support. The task-local probe fills those gaps using the generator's actual declarations instead of a copied rival-name list.

**Alternatives rejected.** A one-off notebook or uncaptured shell snippets would be harder for future agents to replay. Editing shared tools would violate the return scope. Copying a fixed rival list into tests would drift from the production semantic contract.

**Probes.** The probe is itself covered by task tests and returns a machine-readable report. Shared-tool proposals are separated in `FEEDBACK_TO_CODEX.md` as F1 and F2.

**Failure mode/limit.** Task-local probes can be overlooked by generic repository test discovery; this is why the required explicit `task_tests` command and `RESULTS.json` entry are retained.

## D10 — Keep documentation source-bound and explicit about limits

**Decision.** Update `SUMMARY.md`, `notes.md`, and `workspace/README.md` after detecting that the code battery did not catch stale rectangle-only prose.

**Rationale.** A future agent reading the task directory should not infer the obsolete 2.0.1 grammar or axes. Documentation now names the rule hash, exact controls, border overwrite, semantic rivals, and authority boundary.

**Alternatives rejected.** Leaving the old imported summary as historical provenance was rejected because it is presented as current task documentation. Historical baseline bytes remain preserved by the packet and patch.

**Probes.** `checks/documentation-drift.json` records old/new hashes and the exact mismatch. Fresh delta replay verifies the final documentation patch applies cleanly.

**Failure mode/limit.** Documentation can drift again unless shared lint gains a source/doc consistency check (F2).
