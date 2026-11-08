# Current generator account: `f5bef0d462cd`

## Intended rule

The input is a fixed 4×14 analogy split by full color-9 columns into three 4×4 panels. Infer the unique transform that maps panel 0 to panel 1 in the canonical order `id`, `rot90`, `rot180`, `rot270`, `flip-h`, `flip-v`, `transpose`; apply that transform to panel 2. The canonical Racket authority was not changed. `RULE_HASH` is pinned to `9a215441e24b`.

## Current design (`VERSION = 4.0.0`)

- Panel motifs are 4-connected, use one color each, contain 3–5 cells, and have seven distinct transform images. Panel 0 and panel 1 share a color; panel 2 uses a different color.
- Exact public controls are `transform`, `motif_cells`, and `query_cells`. Unknown, mistyped, and out-of-range controls reject. `observe_overrides` reconstructs all three controls from a generated grid.
- The default 20-step transform schedule covers all seven transforms. Every cyclic four-pair lesson has four distinct transforms and includes both `rot90` and `rot270`, so fixed-transform and inverse-direction rules are refuted under every hold-one-out query rotation.
- `motif_cells` follows the difficulty band (3/4/5). `query_cells` varies with seed but remains constant inside a lesson, avoiding an earlier leak in which panel cell counts predicted quarter-turn direction.
- The semantic contract declares nine executable competitors: seven fixed transforms, inverse transform, and return-panel-1.

## Reversed decisions and evidence

1. **Prior:** version 3.2 exposed six nominal controls, accepted unknown overrides, advertised invalid negative textures, ignored difficulty, and did not pin the rule hash. **Now:** three exact observable controls, strict validation, active difficulty bands, no negative textures in the valid domain, and a pinned hash. The final battery is 12/12 green and the override matrix has 5,850 accepted draws with zero findings.
2. **Prior:** independent random transforms could produce a four-pair lesson in which one fixed transform fit every demonstration and changed the query. **Now:** the 20-step schedule guarantees four distinct transforms per cyclic lesson. The retained version-3.2 witness is `counterexamples/baseline_fixed_transform_lesson.json` and is covered by focused tests.
3. **Intermediate:** a shorter schedule still admitted the inverse-transform rival for some rotated queries. **Now:** every four-pair window includes both quarter-turn directions; the focused regression was observed failing before this change.
4. **Intermediate:** sample-index-dependent `query_cells` perfectly encoded `rot90` versus `rot270`. **Now:** query size is seed-dependent and constant within a lesson. The retained red run is `WORK/checks/task-tests-count-shortcut-red2` in the review packet.
5. **Intermediate:** deterministic defaults were semantically correct but omitted keyed draw provenance expected by the shared override checker. **Now:** single-option keyed draws preserve provenance without changing the schedule.

## Verified scope and limits

Final generator SHA-256: `e8cb1a1636f16e626076abc43525df7062d3c4ca8839340d0f06f688a23ffc01`.

The final focused suite has 93 tests. A 300-lesson production census (100 per band) materialized 1,200 pairs and all 1,200 query rotations with zero ambiguity against the declared competitors. A fixed-seed schedule census covered all 20 start residues × 3 bands and 240 rotations with zero ambiguity. These are finite checks against declared rivals, not a proof that every possible learner must infer the intended rule. The grammar intentionally covers the canonical fixed-size sparse-panel family rather than all lawful inputs. Hidden solve-query labels remain unavailable to the reviewer.
## Current reviewer considerations

Source SHA-256: `e8cb1a1636f16e626076abc43525df7062d3c4ca8839340d0f06f688a23ffc01`.

# Decisions for `f5bef0d462cd`

Final generator SHA-256: `e8cb1a1636f16e626076abc43525df7062d3c4ca8839340d0f06f688a23ffc01`.

## D1 — Preserve the canonical rule boundary

- **Prior state:** the generator described the canonical operation but did not pin its rule hash.
- **Choice:** pin `RULE_HASH = "9a215441e24b"`; do not edit canonical data or Racket authority.
- **Reason:** the observed defects were distribution, contract, and lesson-teaching defects. Rule-smoke and authority execution were already behaviorally correct.
- **Rejected alternative:** change the Racket program to fit an easier sampler. That would invert the authority relationship and was unnecessary.
- **Limit:** a pinned hash detects drift but does not itself establish that the input curriculum is useful.

## D2 — Use a fixed canonical shape rather than a nominal size axis

- **Prior choice:** `panel_k` was advertised as an exact control but had only the value 4, so it could not demonstrate override effect.
- **New choice:** remove it from `AXES` and state 4×14 as an invariant.
- **Reason:** all canonical examples use 4×4 panels, and the Racket transform analogy is cleanly represented there. A singleton axis adds contract noise, not data diversity.
- **Alternative:** expand to other square panel sizes. Rejected for this repair because no canonical evidence or morphology tests justified that broader domain.
- **Limit:** the generator does not claim size generalization.

## D3 — Replace six weak controls with three exact observable controls

### `transform`

- **Prior:** advertised, but explicit overrides and unknown keys were not validated; defaults were independently random.
- **New:** exact seven-name enum, strict validation, reconstructable by unique panel-0→panel-1 matching.
- **Reason:** this is the semantic branch that the lesson must teach.

### `motif_cells`

- **Prior:** a `fill` float axis claimed “3..5 cells” but could not be probed as declared.
- **New:** exact integer 3–5, directly observed from panel 0.
- **Reason:** cell count is a legitimate morphology control only when its units and pixel effect are explicit.

### `query_cells`

- **Prior:** no independent query-motif control.
- **New:** exact integer 3–5, observed from panel 2.
- **Reason:** independent source/query morphology prevents accidental equality assumptions and increases shape diversity.

### Removed controls

- `n_distinct_colors=2`, `density=sparse_motifs`, and `panel_k=4` were singleton labels rather than useful axes.
- `texture` mixed lawful generation with `no_dividers`, `empty_panels`, and `single_panel`, all outside the generator's own valid domain.
- **Rejected alternative:** retain them as diagnostic axes. The ordinary sampler needed a truthful minimal public contract; negative fixtures belong in tests, not the valid training domain.

## D4 — Enumerate connected transform-asymmetric supports

- **Prior choice:** choose from six hand-written patterns, several with limited placement diversity.
- **New choice:** enumerate all 4-connected supports of 3–5 cells in 4×4 whose seven canonical transform images are distinct; cache each pool and sample from it.
- **Reason:** construction guarantees unique transform inference, broadens support placement, and eliminates retry/fallback dependence.
- **Alternative:** random cells followed by rejection. Rejected because it makes exact controls and deterministic testing less transparent.
- **Failure mode/limit:** shape pools encode one narrow notion of useful morphology—connected sparse objects—and exclude symmetric but potentially lawful examples.

## D5 — Use a 20-step teaching schedule

- **Prior choice:** sample each transform independently. A retained baseline lesson `[rot90, rot270, rot270, rot270]` let fixed `rot270` fit every demonstration and fail the query.
- **First repair:** use a shorter balanced cycle. A red rotation test showed inverse-transform reasoning could still fit demonstrations composed of self-inverse transforms while changing a quarter-turn query.
- **Final choice:** a 20-step cycle in which every cyclic four-pair window has four distinct transforms and includes both `rot90` and `rot270`.
- **Reason:** with three demonstrations and one query, this locally guarantees a direct witness against every fixed transform and against direction reversal, regardless of which pair is held out.
- **Alternative:** resample lessons until a semantic hook passes. Rejected because a transparent periodic construction is cheaper, reproducible, and exhaustively enumerable.
- **Limit:** it targets declared transform rivals; it is not a proof against arbitrary program synthesis.

## D6 — Make difficulty observable without encoding the label

- **Prior state:** easy/medium/hard were dead; generated bytes were identical for sampled seeds.
- **Initial repair:** band-controlled source count and sample-index-controlled query count. A new leakage test found the count tuple perfectly predicted `rot90` versus `rot270`.
- **Final choice:** difficulty fixes source motif size to 3/4/5. Query size is selected from a band-specific permutation by seed and stays constant across all pairs in a lesson.
- **Reason:** bands now differ, all query counts have support, but the within-lesson nuisance feature cannot identify the scheduled transform.
- **Rejected alternative:** randomize query size independently per pair. That broadens support but creates an unnecessary changing cue inside a lesson and makes leakage analysis harder.
- **Evidence:** `checks/task-tests-count-shortcut-red2/` then final 93/93 tests.
- **Limit:** correlations involving more complex shape features remain possible; the finite leakage regression covers the concrete discovered shortcut.

## D7 — Record deterministic defaults through keyed draws

- **Prior implementation:** default schedule values were computed directly, then observed correctly from pixels.
- **New implementation:** pass each scheduled default through a single-option `draw_choice` under its public axis key.
- **Reason:** the shared override checker requires provenance for exact axes; the first complete after battery failed only that stage.
- **Alternative:** weaken or bypass the checker. Rejected because provenance is useful for replay and does not require semantic change.
- **Limit:** single-option draws are bookkeeping, not randomness.

## D8 — Declare nine concrete semantic competitors

- **Choice:** seven fixed-transform rules, inverse transform, and return-panel-1 are present in all shared semantic maps, with executable witnesses and a lesson-level identifiability hook.
- **Reason:** these are simple, plausible shortcuts induced by the analogy layout and transform inventory.
- **Alternative:** rely only on generic diversity statistics. Rejected because label-correct individual pairs can still form an ambiguous lesson.
- **Limit:** undeclared rivals remain unknown. The 27 census labels are the same nine functions exposed through three contract namespaces, not 27 independent hypotheses.

## D9 — Retain the baseline counterexample

- **Choice:** preserve the exact version-3.2 four-pair lesson, canonical Racket outputs, fixed-`rot270` rival output, source/rule hashes, and a focused regression.
- **Reason:** it demonstrates the teaching defect more directly than aggregate transform counts.
- **Alternative:** keep only prose. Rejected because future changes need an executable failure witness.

## D10 — Audit targets remain read-only

- **`ffe1da16c912`:** document that ordered fourth-query lessons are safe while arbitrary rotations can omit a prototype position. Do not alter the target because the assignment is audit-only.
- **`5ee8de1860a7`:** report no issue found after focused tests and 154,368 rotation checks; do not invent a defect to fill the section.
- **Limit:** both conclusions are bound to the assigned source hashes and finite probes.

## D11 — Solve evidence remains separate from generator evidence

- The blind solve was completed before any prohibited source exposure and declares `earlier-exposure: no`.
- The post-repair solve was generated from the final source hash and honestly declares earlier exposure to the rule family while recording no reference consultation during the solve.
- Both have 3/3 visible-example passes; hidden labels remain unknown.
