# Working notes: 0d6d64e90301

## Current selected behavior (review `review-42c8ad933d52e759`)

- Intended rule: exact nearest-neighbor upscale by factor two; every input cell becomes a 2×2 block.
- Selected authority remains unchanged: `RULE_HASH = 511f58f5d471`.
- Generator version: `3.2.0`; final generator SHA-256:
  `35e1ae4a897c4fde278e2f23abf9f24dc9bbf0f7441af405e00b34caa7828649`.
- Teaching grammar remains canonical-scale 3..5, zero background, exactly two
  visible foreground colors, sparse strict-majority background, and one 4-connected
  motif spanning both axes.
- Exact public controls remain `grid_h` and `grid_w`, each integer 3..5. Invalid
  scalar types, negative indices, invalid difficulty values, unknown keys, and
  out-of-range values now fail loudly.

## Reversed choices

### Canonical-shortcut declaration

**Prior choice:** alias all three per-instance rivals (`tile_each_whole_row`,
`tile_whole_grid_2x2`, `transpose_then_upscale`) as canonical shortcuts.

**New choice:** retain those as instance/lesson competitors, but declare only
`square_only_upscale` as a canonical shortcut. The old three already fail the
canonical examples; the new rival fits all canonical pairs because every
canonical input is square. A lawful 3×4 witness is retained at
`counterexamples/square_only_rectangular.json`.

### Ordinary dimension sampling

**Prior choice:** independently draw difficulty-skewed heights and widths; in
sampled medium lessons this produced only 4×4 squares and allowed the square-only
shortcut to survive.

**New choice:** a period-3 schedule supplies one square anchor, one wide rectangle,
and one tall rectangle. Every 3-pair bundle has two rectangles, so every 2-demo
held-out-query rotation retains a rectangular demonstration. Explicit overrides
still support every 3..5 height/width combination.

## Evidence

- Baseline battery: 10/12 green; defect lint found 84 accepted invalid scalar
  probes and semantic gate rejected false canonical-shortcut declarations.
- Final battery: 12/12 green with required rotations and declared-period
  enumeration (`WORK/checks/final-after/`).
- Task tests: 24/24 passed (`WORK/checks/final-task-tests/`).
- Production census: 300/300 lessons identifiable, 0/900 ambiguous rotations,
  900 unique inputs (`WORK/checks/lesson-census-final.summary.json`).
- Fixed-seed complete schedule: 9/9 lessons and 0/27 ambiguous rotations across
  all start residues/bands (`WORK/checks/lesson-census-schedule-s0.summary.json`).
- Prior return `external-local-random:ccf79d127a3f` was used only as a lead; all
  measurements above bind to the selected source in this packet.

## Parametric assessment

A separate proposed prototype under `workspace/parametric/` varies
`scale_factor` between 2 (canonical/default) and 3 once per episode. Both exact
Racket settings were executed at seed 17; every label matched Racket and each of
the two demonstrations distinguished the selected factor from the alternative.
This prototype does not alter production generation, canonical data, or approval.

## Known limits and open findings

- The named-rival checks are finite and do not prove unique induction against all
  programs, lookup tables, or domain gates.
- Fixed-seed schedule enumeration does not exhaust all seeds or future lesson
  assemblers. External callers can override every pair to square dimensions and
  must preserve the lesson contract themselves.
- The sparse connected two-color grammar is narrower than the Racket rule’s full
  arbitrary-grid domain; this is an explicit teaching choice, not a rule claim.
- Difficulty changes scheduled scale/profile, not a measured model-difficulty
  quantity.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `35e1ae4a897c4fde278e2f23abf9f24dc9bbf0f7441af405e00b34caa7828649`.

# Decisions for `0d6d64e90301`

Finding IDs refer to `REVIEW.md`. The pinned baseline, not an unintegrated historical patch, was the starting point. Prior return `external-local-random:ccf79d127a3f` was consulted only for leads; every adopted claim was rechecked locally.

## D1 — Preserve the selected rule and the sparse connected teaching grammar

**Choice.** Keep `RULE_HASH = "511f58f5d471"`, leave canonical/base authority data unchanged, and retain the 3..5, zero-background, exactly-two-foreground-color, sparse 4-connected motif grammar.

**Original rationale.** The exact historical rationale is not fully retained. Prior notes indicate the grammar was deliberately reconstructed around the canonical examples and that a texture-heavy expansion had already been rejected. The canonical task itself is a per-cell 2× upscale and technically accepts arbitrary rectangular grids, so this grammar is a curriculum choice, not a rule precondition.

**Alternatives considered.** Generate arbitrary colors/textures; use full/dense grids; remove connectivity; or change the Racket authority. Arbitrary input breadth would add nuisance variation without addressing the measured shortcut, while changing the authority would be unjustified because rule smoke and canonical outputs were already correct.

**Probes/evidence.** All three canonical pairs pass `self_check` and `strict_canonical_like`; the final profile, self-check, rule-smoke, and authority-sync stages are green in `checks/after/`. The final authority-set SHA equals the baseline authority-set SHA.

**Failure modes/limits.** The grammar is narrower than the mathematical domain of upscaling. A solver could exploit connectivity, sparsity, or two-color regularity in ways not represented by the four declared rivals. The return does not claim universal rule induction.

## D2 — Reject invalid requests instead of coercing them (R1)

**Choice.** Require exact `int` (not `bool`) for `seed`, `sample_index`, `grid_h`, and `grid_w`; require nonnegative `sample_index`; accept only `None/easy/medium/hard` difficulty; reject unknown overrides and out-of-range axes before sampling.

**Original rationale.** Unknown. The baseline delegated typed draws to `gen_ctx`, but 84 linter probes showed that coercible strings/floats, booleans, negative indices, and invalid difficulty values could be accepted.

**Alternatives considered.** Preserve permissive coercion for compatibility; rely only on downstream `draw_int`; or validate only public axes. These were rejected because a deterministic generator contract should fail loudly and because call-level scalars influence replay identity just as much as overrides.

**Probe.** The parameterized regression first failed against the baseline behavior, then passed after one validation layer was added. Final defect lint is empty/green and the explicit task-test run passes 24/24.

**Failure modes/limits.** Existing callers that relied on undocumented coercion now receive `TypeError`/`ValueError`. This is intentional. Validation does not attempt to canonicalize NumPy integer subclasses; exact built-in integers are the supported public contract.

## D3 — Separate canonical shortcuts from instance-local rivals (R2)

**Choice.** Keep three instance-local competitors (`tile_each_whole_row`, `tile_whole_grid_2x2`, `transpose_then_upscale`) but stop calling them canonical shortcuts. Declare the actual canonical-fitting rival `square_only_upscale`: it performs 2× upscaling only when height equals width and otherwise returns the input unchanged.

**Original rationale.** Unknown. The baseline aliased all semantic rivals into `CANONICAL_SHORTCUTS`, but its own canonical examples refuted each of the three entries. Because every labeled canonical input is square, domain gating on squareness is a stronger and genuinely canonical-compatible hypothesis.

**Alternatives considered.** Remove `CANONICAL_SHORTCUTS`; relabel the three old rivals without adding a canonical one; or use a more contrived lookup-table rival. Removing the category would hide the real underdetermination. A square-domain gate is simple, plausible, and exactly motivated by the canonical support.

**Probe.** The focused test executes `square_only_upscale` on every canonical pair and requires exact equality with the canonical output. The lawful 3×4 grid in `counterexamples/square_only_rectangular.json` passes both validators, while the intended output is 6×8 and the rival leaves it 3×4. The final semantic gate verifies the declared canonical claim and witness.

**Failure modes/limits.** Other canonical-compatible gates exist (specific dimensions, palettes, densities, memorization). This rival is “strongest plausible” in the sense of simple domain generalization, not a proof that no stronger program fits.

## D4 — Replace unstructured dimensions with a three-step teaching schedule (R3)

**Prior choice.** Heights and widths were independently difficulty-skewed over 3..5; medium effectively produced only 4×4 examples in the sampled semantic run. A two-demo lesson therefore could contain only squares and fail to distinguish `square_only_upscale`.

**New choice.** Declare `LESSON_SCHEDULE_PERIOD = 3` with one square anchor, one wide rectangle, and one tall rectangle. Band-specific dimensions remain canonical-scale: easy `(3×3, 3×4, 4×3)`, medium `(4×4, 4×5, 5×4)`, hard `(5×5, 4×5, 5×4)`. Any three consecutive pairs contain two rectangles, so holding out any one as query leaves at least one rectangular demonstration.

**Reason.** The first semantic probe found 8/12 ambiguous lessons and no medium-band rectangle. Random resampling could improve average frequency but could not guarantee that every two-demo bundle refuted the shortcut.

**Alternatives considered.** Make every input rectangular; increase `EXAMPLES_NEEDED`; rejection-sample whole lessons until a rectangle appears; or keep random dimensions and accept ordered-only curricula. All-rectangular lessons would drop canonical square anchors. More demonstrations increase cost. Bundle-level rejection is harder to reason about and replay. The three-step schedule is the smallest deterministic guarantee while retaining square and rectangular support.

**Probe.** A schedule regression checks every three-step window and every query position. The strict enumerated semantic gate passes 12/12 smoke lessons and 0/36 ambiguous rotations. The 100-per-band census passes 300/300 production lessons and 0/900 rotations. The fixed-seed complete-period census passes all 9 lessons and 27 rotations.

**Failure modes/limits.** The schedule is visible and deterministic; it should not be interpreted as an estimate of natural shape frequencies. Fixed-seed period enumeration does not exhaust all seeds, rejected-draw behavior, future materializers, or undeclared rivals. Explicit `grid_h/grid_w` overrides can request square-only examples, so callers assembling custom lessons must preserve the teaching contract themselves.

## D5 — Retain exact overrides while scheduling ordinary draws

**Choice.** Ordinary draws use singleton strict draws at scheduled dimensions so replay metadata still records the selected axes. Explicit overrides continue to accept every integer combination in 3..5, independent of difficulty, and `observe_overrides` recovers the exact shape from pixels.

**Original rationale.** The baseline advertised both axes as exact controls. Removing them to simplify the schedule would be a compatibility and coverage regression.

**Alternatives considered.** Narrow each band’s override domain to its scheduled shapes; silently ignore overrides during scheduled lessons; or expose a new `profile` axis only. These would either contradict `AXES`, hide caller intent, or unnecessarily break existing exact controls.

**Probe.** Boundary override tests request 3×3 and 5×5 in every band, validate the generated grids, and verify round-trip observation. Final override gate is PASS with no findings or warnings.

**Failure modes/limits.** A caller can deliberately override all pairs to squares and reintroduce R3. The production sampler is safe; arbitrary external assembly is outside the schedule guarantee.

## D6 — Keep finite rival checks executable and explicit

**Choice.** Use the same four pure functions in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`; map each semantic witness to the rival it is intended to refute; have `lesson_identifiable` verify labels and check whether a rival survives demonstrations but changes the query.

**Original rationale.** The baseline already had executable rivals, but its canonical classification was invalid and it lacked the square-domain witness.

**Alternatives considered.** Describe shortcuts only in prose; rely only on per-grid witness frequency; or compare only the production query. Prose cannot be regression-tested, and witness frequency does not prove that each complete lesson contains the distinguishing evidence. Testing every held-out query position is stronger for a reorderable curriculum.

**Probe.** Final semantic reports and both lesson censuses retain rival-by-rival results and exact materialized lessons.

**Failure modes/limits.** Named rivals are not an exhaustive program space. Function aliases are checked under the census tool’s documented callable/name caching semantics. Semantic equivalence beyond exact outputs is not analyzed.

## D7 — Return scale factor 2 versus 3 as a separate prototype (P1)

**Choice.** Treat nearest-neighbor scale as the one small meaningful rule parameter. Allowed values are `{2,3}`; 2 is canonical/default. The prototype chooses once per episode by seed parity, uses two demonstrations plus one query, and materializes an exact Racket program for each setting.

**Original rationale.** The canonical rule hardcodes factor 2. The packet asks for a small parameter assessment but explicitly forbids silently turning a fixed per-puzzle generator into a production parametric API.

**Alternatives considered.** Parameterize colors, motif density, or input dimensions; these alter presentation, not the executed transformation. Parameterize anisotropic factors or arbitrary `k`; those broaden the family more than needed. Factor 3 is the smallest recognizable alternative.

**Probe.** `checks/parametric/scale-factor-seed17.json` records actual Racket outputs, exact programs and hashes. For both settings, all three labels matched Racket and both demonstrations disagreed with the alternative. Prototype task tests pass in `checks/parametric-tdd-green/`.

**Failure modes/limits.** One retained seed and two settings are bounded evidence. A model may infer output size immediately; that is acceptable because the parameter is meant to be demonstrable. The prototype is proposed only and does not modify production selection, canonical rows, or approval.

## D8 — Keep evidence for failed iterations

**Choice.** Retain the baseline battery, TDD-red runs, the first ambiguous semantic gate, the non-enumerated schedule warning, and prototype-red run rather than presenting only the green endpoint.

**Reason.** These records establish that the regressions could catch the defects and show why each design change was made.

**Evidence.** `checks/before/`, `checks/tdd-red/`, `checks/tdd-red-schedule/`, `checks/semantic-gate-1/`, `checks/semantic-gate-2/`, and `checks/parametric-tdd-red/`.

**Limit.** Some controller invocations were externally interrupted after writing valid stage receipts; the final hash-bound battery was resumed unchanged and completed. The final aggregate—not an interrupted intermediate—is the passing claim.
