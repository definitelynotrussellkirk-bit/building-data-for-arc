# Current design and review notes: 699479899861

## Intended rule

Treat each 4-connected red (`2`) component independently. Recolor every cell in that component's row/column Cartesian closure green (`3`); for a 4-connected component this is exactly its axis-aligned bounding box. Preserve all cells outside those component boxes, including unrelated decorative colors. The canonical Racket authority remains unchanged at `RULE_HASH = ac41730bf8e3`.

## Distribution and lesson design

The four-slot schedule intentionally provides: a canonical anchor; a noncanonical component extent; a three-component mixture; and a four-component mixture. Across a four-demonstration lesson these slots distinguish per-component closure from a global box, first-component-only handling, fixed canonical 3×2 geometry, retaining red while adding green, and erasing decorations. Exact public axes remain `grid_h`, `grid_w`, and `n_blobs`; unknown overrides are rejected.

## Proposed native family: one or two closure rounds

`workspace/parametric/` now supplies a native adapter, promotion contract, exact
canonical resource, source/evidence inventory, reproducible finite-rival audit,
and a source-bound single-query public projection tool. `closure_rounds=1`
returns the exact canonical program; `2` first fills red boxes green, then
recomputes green 4-components from that completed snapshot and fills their
boxes. First-pass boxes can merge previously separate red objects, so the
second transformation depends on the updated state. Its snapshot semantics
also differ from updating components after each individual fill.

Both settings use identical inputs for matching seed/split/index, support
independent 2–6 demos and 1–4 queries, and preserve prefixes. Four-query profiles
include substantive 30×30 content touching all boundaries. The separate grammar
contains 8–10 red components and L/plus/U/zigzag/T topologies; this extends the
production sampler rather than changing its approved source or advertised axes.
The two-demo minimum uses 16×17 and 18×20 canvases to carry several independent
distinctions. Further demos/queries support all eight dihedral orientations.

**Teaching reversal retained:** Initially random chain orientations passed a
13-rival audit but allowed a plausible live-update scan to fit all demos and
change queries. Seed 0 with two demos and seed 17 with the reverse scan reproduce
the defect; `checks/699479899861/live-scan-before/live-scan-counterexample.json`
contains six protected-Racket executions of the original lesson. The first two
demonstrations now construct opposite chain orientations: demo 0 refutes the
ascending scan, demo 1 the descending scan, without increasing the demo count.
The exact regression failed before repair and passes afterward. Component-count
and topology variation was also added to avoid an all-L, fixed-eight sampler.

Final prototype SHA-256:
`0c54c61e9475aa8f36bfe1213dfeb9b87c34d9dd1cf2596fec8ce720ef267e06`.
Final source-current evidence is `checks/699479899861/self-review-v2/`: 80
requests, 640 sampled pair occurrences, 200 distinct inputs, 480 protected
Racket evaluations over eight episodes and 15 executable rivals, with no
remaining tested ambiguity or Python/Racket mismatch. All sampled 30×30 pairs
have at least 134 foreground cells across all four quadrants. The final staged
task suite passed 79 tests (`checks/699479899861/task-tests-final/`). Earlier
13-rival and 74-test receipts describe superseded prototype bytes only.

Native qualification passed both settings on seeds 0/17, three demos and four
queries, with 40 protected evaluations. See
`checks/699479899861/qualification/{qualification,execution}.json`.
`checks/699479899861/causal/` contains two native-built, protected-replayed cases:
stale original components and a descending live scan give different final grids.
The authored intermediate explanations remain reviewer arguments, not proofs
of universal algorithmic depth. `checks/699479899861/sequential-public/` holds
16 verified one-query views; all answers/settings/order/receipts are private.

The exact canonical rule hash `ac41730bf8e3` and production generator SHA
`2354d2dd1bb12333428c3ff34af3c0ce0843f1bc71a0fb32610ed75795f9c706`
are unchanged. No prior audit status is cleared. This family is **reviewer-ready,
owner acceptance pending**, and training remains inactive. The next action is
owner integration followed by native qualification and fresh acceptance on the
exact live source. `workspace/parametric/README.md` has reproducible commands,
the admitted grammar, and explicit finite-check/projection limits.

## 2026-10-11 repair

Prior source SHA-256 `024fdd4b4b06b6232c2f3c329b8b2aad0c50c096656760e013969507fc9659cb` accepted boolean and negative `sample_index` values because modulo arithmetic happened before strict validation. The repaired generator rejects any `sample_index` whose exact type is not `int` or whose value is negative. Final generator SHA-256 is `2354d2dd1bb12333428c3ff34af3c0ce0843f1bc71a0fb32610ed75795f9c706`.

The prior audit `review-42e97d9689a2fa8c:v0001` correctly identified that task-local tests used repository-only imports and paths. Those tests now use `reviewer_support.find_root`, `load_selected_generator`, `canonical_pairs`, and the public `Catalog` API, so they run in the isolated portable runtime. A regression test covers strict `sample_index` handling.

## Retained shortcut counterexample

`counterexamples/fixed_canonical_3x2_boxes.json` records seed `0`, sample index `1`, difficulty `easy`. The rival that always paints a canonical 3×2 or 2×3 box fits all five canonical pairs, but on this lawful generated input it wrongly paints `(5,3)` and `(5,4)` green. The selected Racket output was retained in `checks/shortcut-witness/racket.json`, and the task-local suite replays the recipe, canonical fit, rival output, and Racket result.

## Verification and limits

The final source passed all 12 battery stages and 13 portable task tests. A 300-lesson census (100 per band, four demonstrations plus one query, all five query rotations required) materialized 1,500 unique inputs and found zero ambiguities against the declared rivals in production ordering or rotations. This finite census does not prove uniqueness against undeclared hypotheses or all random seeds. The generator's teaching schedule and canonical authority were not changed by this repair.
## Current reviewer considerations

Source SHA-256: `2354d2dd1bb12333428c3ff34af3c0ce0843f1bc71a0fb32610ed75795f9c706`.

# Decisions for 699479899861

## D1 — Preserve the canonical rule and current lesson architecture

**Original rationale.** The imported design notes establish that row/column Cartesian closure equals bounding-box fill for a 4-connected component, and that the four-role schedule deliberately teaches component separation, noncanonical extents, recoloring, and decoration preservation.

**Probe.** Baseline rule smoke, semantic gate, profile floor, override checks, grammar checks, Racket lint, and authority sync all passed. The only battery failure was strict scalar handling.

**Alternatives rejected.** Rewriting the Racket rule or replacing the schedule would add risk without addressing the observed defect. Adding new public axes would weaken the existing exact-observability contract.

**Decision.** Leave the Racket authority, `RULE_HASH`, AXES, component grammar, and four-role schedule unchanged.

**Failure mode/limit.** Passing declared-rival checks does not certify uniqueness against undeclared rules. This remains documented rather than overclaimed.

## D2 — Validate `sample_index` at the public boundary

**Observed failure.** The baseline `defect_lint` accepted `True`, `False`, and `-1`; a focused RED test reproduced all three. Python booleans subclass `int`, and negative values have well-defined modulo results, so validation after `% 4` would be too late.

**Alternatives considered.** Relying on `gen_ctx` did not reject these values on this path. Using `isinstance(sample_index, int)` would still accept booleans. Coercing with `int()` would silently change caller input and retain ambiguous behavior.

**Decision.** Require `type(sample_index) is int` and `sample_index >= 0`, raising a `ValueError` containing `sample_index` before schedule arithmetic.

**Evidence.** `checks/task-tests-red/result.json` is the failing pre-fix test; `checks/task-tests/result.json` and the final clean task-test run are green; final defect-lint passes.

**Failure mode/limit.** This repair intentionally rejects numeric subclasses and integer-like strings rather than normalizing them. That matches the strict scalar contract used by the shared linter.

## D3 — Port task tests through public, source-bound helpers

**Observed failure.** The previous test computed a task-local `ROOT`, then appended repository-layout paths below it. In the staged runtime that produced nonexistent nested paths and failed before collection. It also imported legacy `scripts.generator_module_loader`, `scripts.rule_smoke`, and a direct Racket bridge.

**Alternatives considered.** Copying more repository paths into the test runtime would preserve brittle coupling. Guessing a different fixed `parents[n]` depth would fail in another layout. Skipping canonical exactness would reduce coverage.

**Decision.** Use `find_root(__file__)`, `load_selected_generator`, `canonical_pairs`, and `Catalog`. These APIs bind source, canonical data, and selected authority to the runtime manifest while preserving exact canonical/reentrancy checks.

**Evidence.** The before task-test report fails preflight/collection. The repaired suite first reached 9 passing tests and the three intentional RED failures, then passed 12/12 after the production fix and 13/13 after adding the retained counterexample.

**Failure mode/limit.** Portable tests still depend on the controller's documented runtime contract. They no longer depend on a particular repository depth or private import alias.

## D4 — Retain the strongest canonical shortcut as executable evidence

**Hypothesis.** Every canonical red component is a four-cell L with a 3×2 or 2×3 box, so a solver could always paint that fixed-size rectangle rather than infer each component's actual extent.

**Probe.** The tool iterated the generator's declared `CANONICAL_SHORTCUTS`; `fixed_canonical_3x2_boxes` matched all five usable canonical pairs. A scan found the first lawful generated disagreement at seed `0`, sample index `1`, difficulty `easy`. The selected Racket rule was applied through the supported `arcpuzzles apply` command.

**Decision.** Store the exact input, official output, rival output, source hashes, and differing cells in `counterexamples/fixed_canonical_3x2_boxes.json`; replay it in the portable task suite.

**Alternatives rejected.** A global bounding-box rival and retaining-red rival are easier to refute from the canonical demonstrations. The fixed-size rival is stronger because it exactly exploits a canonical regularity.

**Failure mode/limit.** The recorded case establishes one exact disagreement and generator support, not a frequency estimate. Wider support is measured separately by the lesson census.

## D5 — Require query rotations in the lesson census

**Rationale.** The production lesson order is intentionally four-slot, but a learner-facing system may rotate which materialized pair is queried. Individual witness frequency is insufficient; each complete lesson must refute rivals at every permitted query position.

**Decision.** Run 100 lessons per band with four demonstrations, one query, and `--rotate-query` under the required rotation policy.

**Result.** 300/300 lessons, 1,500 pairs/unique inputs, 0 production ambiguities, 0/1,500 rotation ambiguities, and no materialization, hook, or scoring errors.

**Limit.** This random census does not exhaust every seed or undeclared rival. The generator does not declare `LESSON_SCHEDULE_PERIOD`, so no separate period-enumeration claim is made.

## D6 — Keep audit targets read-only

The two drawn audits were independent of the repair. I ran source-bound combined, lint, defect-lint, and direct API probes but made no changes to either target. Findings are recorded in `AUDIT.md`; their failures do not block acceptance of the selected generator patch.

## D7 — Replay the exact return patch on a fresh packet

**Risk.** A green working tree does not prove that the generated return patch applies cleanly or contains every intended new file.

**Decision.** Build a preliminary return, extract its exact `patches/source.patch`, initialize Git inside `WORK/` of a fresh extraction, run `git apply --check` and `git apply`, compare every patched file byte-for-byte with the final workspace, and rerun the portable task suite there.

**Result.** The four expected paths applied exactly, the fresh generator SHA matched `2354d2dd1bb12333428c3ff34af3c0ce0843f1bc71a0fb32610ed75795f9c706`, and all 13 tests passed. Evidence: `checks/fresh-replay/replay.json` and `checks/fresh-replay/changed-paths.json`.
