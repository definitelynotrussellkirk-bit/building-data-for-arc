# 78e3f26e92aa reviewer notes

## Intended rule

The input is a 22–24 by 17–20 color-0 grid with two separated, one-cell-wide vertical bars of equal height in green (3) and an analogous pair in cyan (8). The two color pairs have disjoint row spans. For each color, the pair's bounding-box height is the vertical step size: above and below the bars, rays continue from the outer columns and move one column outward for each full bar-height of vertical distance. The output is 3 or 8 on a single color's rays, 6 at overlaps, and 0 elsewhere. Canonical authority is pinned by `RULE_HASH = ed1ed1d0980e`.

## Reversed prior choice

Version 2.0.1 sampled one solid rectangle per color on 10–20 square grids, always green above cyan, and advertised destructive `texture` values. Its `self_check` only counted colors, so these examples could be labelled by the rule but did not reproduce the canonical four-bar visual grammar. Version 3.0.0 replaces that distribution rather than broadening the checker around it. The minimal retained reproducer is `counterexamples/legacy_two_rectangles.json`; focused tests require both structural checkers to reject it.

## Current distribution and decisions

- Eight deterministic schedule profiles are used. The first four are the four canonical size/geometry anchors; four crossed companions break accidental one-to-one correlations among height and gap axes.
- Every lesson uses three demonstrations (`EXAMPLES_NEEDED = 3`). The schedule covers both vertical orders, height-1 and height>1 bars, and both zero-intersection and intersection branches.
- `easy`, `medium`, and `hard` select distinct lawful placements without changing the declared axis domain. Exact overrides remain constructive in every band.
- Declared axes are only the eight observable structural values. Unknown keys, booleans-as-integers, out-of-range values, and invalid top-level arguments fail loudly.
- Placement pools are cached with a bounded `lru_cache(maxsize=64)` so the exhaustive override gate can exercise all 53,190 calls without narrowing the domain.
- `self_check` and `strict_canonical_like` independently validate rectangularity, palette, four connected one-cell-wide bars, shared same-color row spans, margins, horizontal gaps, disjoint color spans, vertical gap, and dimensions.
- The independent `workspace/reference_probe.py` does not call production geometry helpers. It extracts canonical/generated topology and computes the rule from connected components for future source-bound review.

## Semantic contract

The finite declared rivals are `unit_height_steps`, `downward_only`, and `no_magenta_intersections`. Witnesses explicitly cover height-scaled steps, bidirectional rays, and magenta overlaps. `lesson_identifiable` checks that all three rivals are refuted by the demonstrations and that the query is lawful. This is evidence against those named rivals, not a proof of unique induction against every possible rule.

## Authority synchronization

The canonical rule semantics did not change. The two selected `racket_target.target_code` fields were changed from a manually reviewed behaviorally equivalent alternate expression to the exact canonical `program_solution` bytes; archival `raw_code` stayed unchanged. Evidence is in `checks/manual-authority-sync-review.json` and `checks/authority-sync-already.json`.

## Final evidence and limits

Generator SHA-256: `0e7493ac2619602a3a6a7e3f6d060c29fc67bcb78797039efd4493a2e632a181`.

The final 12-stage after battery is all green; task-local tests are 63/63; the override matrix accepts 53,190/53,190 legal draws; the strict semantic gate records 600/600 canonical-like draws and 12/12 identifiable three-demo lessons with 0/48 ambiguous query rotations. A larger census materialized 300 lessons (100 per band), 1,200 labelled pairs, and 1,200 rotations with zero declared-rival ambiguity. See `checks/after-final/`, `checks/task_tests-final/`, `checks/lesson-census-final.summary.json`, and the compressed source-bound full report mapping in `checks/lesson-census-final.compression.json`.

Known limit: placements and schedules are finite and intentionally canonical-shaped. The declared-rival and generic-mutation checks do not establish universal identifiability or exhaust every legal placement sequence.
## Current reviewer considerations

Source SHA-256: `0e7493ac2619602a3a6a7e3f6d060c29fc67bcb78797039efd4493a2e632a181`.

# Decisions for 78e3f26e92aa

## D1 — Replace the distribution instead of weakening the canonical contract

**Prior choice:** one filled rectangle of color 3 and one of color 8, on smaller square grids. The likely rationale is unknown; it may have been an attempt to generalize the Racket bounding-box rule.

**New choice:** generate exactly the canonical four-bar topology: two one-cell-wide equal-height bars per color, legal same-color gaps, disjoint vertical spans, canonical dimension range, and either vertical color order.

**Reason:** the task's training value depends on inferring the transformation from the same object grammar as the source examples. A broad rule-lawful input is not automatically a source-lawful teaching input. The independent probe and all canonical pairs show the topology mismatch (`checks/reference-probe.json`; `checks/generator.before.py`).

**Rejected alternative:** retain rectangles and only strengthen labels/self-check. That would continue teaching a visually different family and would not exercise same-color pair geometry. Another rejected alternative was to mix rectangles and bars; it broadens support before the canonical behavior is reliably represented and risks teaching bounding-box artifacts.

**Failure mode/limit:** exact canonical-shaped grammar is intentionally narrower than every grid the Racket program can process. This is a distribution decision, not a claim that other inputs are semantically invalid.

## D2 — Use strict, observable structural axes

**Choice:** expose only `grid_h`, `grid_w`, `green_height`, `green_gap`, `cyan_height`, `cyan_gap`, `vertical_gap`, and `color_order`. Reject unknown keys, invalid scalar types (including booleans as integers), and out-of-range values.

**Reason:** each axis is independently recoverable from the generated grid via `observe_overrides`; no hidden texture alias or destructive mode remains. The final override matrix validates all 53,190 legal calls with no declared incompatibilities.

**Rejected alternative:** preserve the legacy `texture` API for compatibility. Its destructive values (`single_bar`, `bars_overlap`, `full_grid`) violate the invariant, and its benign values controlled placement in ways not directly represented in the canonical task.

**Failure mode/limit:** the full Cartesian domain is constructive, but placement choice is not itself an advertised override. The generator does not enumerate every possible placement in default lessons.

## D3 — Preserve four canonical anchors, then decorrelate

**Choice:** profile indices 0–3 are canonical anchors; indices 4–7 cross height and gap values.

**Reason:** the first schedule version reproduced the four canonical profiles but tied several axes one-to-one. The defect checker correctly flagged that a learner could associate one value with another without learning the rule (`checks/axis-lock-red.log`). Crossed companions preserve recognizable anchors while providing one-to-many mappings.

**Rejected alternatives:** randomize all axes independently (less reproducible teaching coverage and harder branch guarantees), or keep only four anchors (axis-lock shortcut remains).

**Failure mode/limit:** eight profiles are not exhaustive. The exhaustive guarantee applies to exact overrides, not to default schedule frequency.

## D4 — Make difficulty distinct without changing semantic support

**Choice:** all bands share the same axis schedule and legal placement pool; difficulty selects different deterministic offsets when at least three placements exist.

**Reason:** the old repair attempt left difficulty byte-identical, which the dead-band regression exposed (`checks/dead-bands-red.log`). Changing geometry ranges by band would make the override contract band-dependent and could create spurious difficulty cues. Placement-only variation adds diversity while preserving rule coverage.

**Rejected alternative:** easy/medium/hard use progressively larger grids or bars. Canonical dimensions are narrow, and band-specific ranges would restrict support and risk leakage.

**Failure mode/limit:** for an exact override with fewer than three lawful placements, bands may necessarily coincide. The generator prioritizes constructiveness over artificial distinction; the tiny-pool regression protects this case.

## D5 — Require three demonstrations and test rotations

**Choice:** `EXAMPLES_NEEDED = 3`, with a schedule that refutes `unit_height_steps`, `downward_only`, and `no_magenta_intersections` in every lesson. Query rotation is required in strict verification.

**Reason:** the rule has three independent teaching obligations: height-scaled horizontal motion, rays on both sides of the bars and in both vertical directions, and magenta overlap semantics. Three demos allow the schedule to cover both intersection branches and both color orders without relying on a lucky query.

**Rejected alternative:** two demonstrations. It may work for selected starts but provides less room to distinguish all three plausible rivals robustly. Four demonstrations add cost without evidence of additional value against the declared set.

**Probe:** final semantic smoke: 12/12 lessons and 48/48 rotations identifiable. Larger census: 300/300 lessons, 1,200/1,200 rotations, and each rival refuted 100/100 per band.

**Failure mode/limit:** these results cover the declared rivals and bounded generic mutations only. They do not prove uniqueness against all hypotheses.

## D6 — Cache legal placements, not outputs

**Choice:** use a bounded `lru_cache(maxsize=64)` for immutable placement pools keyed by structural axes, then choose a deterministic index per call.

**Reason:** the first correct implementation regenerated and shuffled every placement, causing the 53,190-call override gate to exceed five minutes (`checks/generation-performance-red.log`). Caching the domain preserves exact support and deterministic replay while reducing repeated work by roughly two orders of magnitude.

**Rejected alternative:** shrink the override domain or declare legal combinations incompatible. That would hide a performance defect by reducing coverage. Caching full output grids was also rejected because it would consume more memory and entangle seed/sample behavior.

**Failure mode/limit:** the cache is process-local and bounded; unusual sequences of more than 64 distinct axis tuples may evict entries and recompute them, which affects speed only.

## D7 — Independent validation and oracle

**Choice:** production `self_check` uses a structural analyzer; tests and `workspace/reference_probe.py` independently parse components and compute outputs.

**Reason:** a checker that shares all production helpers can reproduce the same bug. The old checker accepted any appearance of colors 3 and 8. The external probe validates canonical support, component count, geometry, and labels without trusting the production solver.

**Rejected alternative:** assert only that Racket labels equal generated labels. This detects label drift but not the wrong input grammar—the original defect.

**Failure mode/limit:** the probe encodes the reviewed canonical topology, so intentionally broad-but-valid future distributions may need an explicit support policy rather than exclusivity.

## D8 — Synchronize selected authority text, preserve archival source

**Choice:** copy the exact canonical `program_solution` into the two selected `racket_target.target_code` fields after manual token-level review; do not modify `raw_code`.

**Reason:** the authority-sync gate requires selected source to be bound to canonical authority. The old selected source was behaviorally equivalent but used different primitives (`apply min/map`, `grid-from-fn`, and `if/not`). The reviewed mapping is recorded in `checks/manual-authority-sync-review.json`, and the final tool report confirms exact synchronization.

**Rejected alternative:** change the canonical rule or archival source. There was no semantic defect requiring that, and archival provenance must remain intact.

**Failure mode/limit:** the manual equivalence review supports why synchronization was safe; the final claim is exact token identity and executable gate success, not a general-purpose Racket equivalence theorem.

## Task-local parametric extension — review-dc456ca305af3afe

The canonical v3.0.0 generator and canonical rule remain byte-for-byte
unchanged. A separate prototype under `workspace/parametric/` adds two small
rule parameters with canonical default `(step_multiplier=1,
overlap_color=6)`: multiplier 2 slows outward ray steps to every two bar
heights, and overlap color 2 recolors only double-reached cells. The four
settings keep the same canonical-shaped input grammar and are fixed once per
episode.

Each retained episode has three demonstrations selected to refute all three
other settings before query labels are considered, followed by four distinct
queries. Labels and receipts come from the matching protected-Racket program.
The opt-in writer hashes exactly the visible public bytes, hides setting/seed/
program/query outputs in private files, rejects duplicate public payloads, and
sorts manifests by public ID. An offline verifier rechecks projection, source
hashes, support, Python parity, identifiability, and receipt binding.

Final retained evidence is `checks/parametric/run-1704/`: four settings, 28
Racket applications, and all verifier checks pass. The focused task suite is
89/89. Prototype source SHA-256 is
`0fedf87f712b1190f8327994cb46dc7d1ed00c0f6170fb236bdc6321f2c67d4a`;
test SHA-256 is
`8b94065b27745f3c793172601a247564135aace7e5c0c6ce0dbb2f95a0f91fb4`.
This evidence supports a prototype handoff only, not production promotion,
approval, or training admission. Next action: independent review of parameter
semantics and the public/private export boundary.
