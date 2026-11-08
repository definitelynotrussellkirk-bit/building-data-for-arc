# Working notes: df74e338b4f5

## Current rule and source

- Generator version: `2.0.0`.
- Final generator SHA-256: `c464c7b69ddbca31d8f58c27be9beeb4d4c15bf0f9ea0a70db3bb245bca429e9`.
- Canonical rule pin: `RULE_HASH = "3ba84d8589ae"`; the Racket authority was not changed.
- Intended transformation: keep background and complete color-9 rectangular frames unchanged; recolor each same-colored marker by the number of frame interiors that strictly contain it.

## Prior lead and reproduced defects

I used retained audit `review-705b00dde5af0be2:v0001` only as a lead, then reproduced its claims against the selected baseline SHA `374fbf52b1f9c4606bffd2541c27a15c3c703285c23b8b77919261c705853d00`. The baseline battery was 6 green, 1 advisory, and 5 failed. It lacked `RULE_HASH`, `self_check`, exact observable controls, and a strict semantic contract. Its frames were packed against the canvas boundary, so the wrong `canvas_edge_distance_depth` rule matched generated examples.

## Repair decisions

- Frames are now constructed as offset, asymmetric, strictly nested rectangles with a blank moat; they are not tied to the canvas boundary.
- Every ordinary example contains decisive marker depths and a depth-zero marker that separates true frame containment from canvas-edge distance.
- Advertised exact controls are only `grid_h=11..18`, `grid_w=11..18`, and `n_frames=2..3`. Calls reject unknown keys, coercions, invalid difficulties, and invalid sample indices.
- Three frames on grids where both dimensions are 11 or 12 are explicitly incompatible because the required exterior shortcut witness cannot be placed without violating the frame/moat grammar.
- `self_check`, `strict_canonical_like`, `observe_overrides`, `rule_mirror`, executable rivals, witnesses, and `lesson_identifiable` all use the same analyzed frame-containment semantics.
- Four demonstrations precede one query. The six-position profile schedule makes every five-pair lesson and every tested query rotation refute all three declared competitors: canvas-edge distance, constant one, and inside-any-frame.

## Reversed decision

An intermediate version put `canvas_edge_distance_depth` in `CANONICAL_SHORTCUTS`. The task-local semantic probe showed that this rival fails canonical training pair 3, so it is not a canonical shortcut. The final source leaves `CANONICAL_SHORTCUTS` empty and retains canvas-edge distance only as a generated-lesson competitor. Evidence: `checks/final-semantic-probe.json` and the retained red probe test log.

## Verification and limits

- Final battery: 12/12 stages green.
- Focused portable tests: 47/47 passed.
- Semantic gate: 600/600 generated inputs strict; 5/5 canonical inputs accepted.
- Lesson census: 300 four-demo lessons, 1,500 unique labeled pairs, and 1,500 held-out query rotations; zero declared-rival ambiguities, hook warnings, materialization errors, or scoring errors.
- A minimal lawful counterexample to the old canvas-distance shortcut is retained at `counterexamples/canvas_edge_distance_depth.json` and covered by tests.
- `workspace/probe_semantics.py` is a reusable source-bound checker for declared canonical shortcuts, lesson competitors, and semantic witnesses.

The finite rival set is not a proof of unique induction against every possible hypothesis. The generator intentionally covers 11..18 grids, two or three frames, one marker color, and 2..8 markers rather than every canonical-looking construction. No selected-generator finding remains open.
## Current reviewer considerations

Source SHA-256: `c464c7b69ddbca31d8f58c27be9beeb4d4c15bf0f9ea0a70db3bb245bca429e9`.

# Decisions for df74e338b4f5

## D1 — Preserve the authority rule

**Choice.** Keep the Racket transformation unchanged and pin `RULE_HASH = "3ba84d8589ae"`.

**Why.** All five canonical labeled pairs support strict frame-containment depth, and the retained counterexample was a generator-distribution failure, not an authority-label failure. Final authority synchronization and 120/120 Racket/mirror parity checks are green.

**Rejected alternative.** Changing the rule to canvas-edge distance would fit the old generated distribution but contradict canonical data and the task's written semantics.

## D2 — Construct geometry from the semantic grammar

**Choice.** Build two or three complete color-9 rectangular frames with independent offsets and at least one blank-cell moat between successive outlines.

**Why.** The baseline's canvas-boundary start and regular insets made frame depth recoverable without detecting frames. Offset/asymmetric boxes preserve the intended objects while breaking that shortcut.

**Probe.** `counterexamples/canvas_edge_distance_depth.json` is lawful under `self_check`; the authority/mirror output differs from the old rival at the retained exterior marker.

**Rejected alternative.** Randomly shifting the entire old concentric template would still retain regular canvas-distance correlations and would not guarantee a decisive counterexample.

## D3 — Make semantic evidence constructive, not probabilistic

**Choice.** Select markers from analyzed depth regions and guarantee a depth-zero anti-shortcut witness plus multiple containment depths in every ordinary draw.

**Why.** Rejection sampling could silently degrade or fail at small dimensions. Constructive placement makes the lesson contract deterministic and makes failures attributable to incompatible geometry rather than retry luck.

**Limit.** The grammar intentionally uses one marker color and 2–8 marker cells. It does not try to span every superficially similar scene.

## D4 — Declare the exact legal control surface

**Choice.** Advertise only `grid_h=11..18`, `grid_w=11..18`, and `n_frames=2..3`; validate genuine integers, reject unknown controls and unsupported difficulties, and expose exact realized values through `observe_overrides`.

**Why.** The old metadata described a broader domain than each band actually honored. Exact observability is more useful for controlled data generation than band-dependent silent clamping.

**Joint incompatibility.** Three frames require an 11×11 frame footprint and an exterior decisive witness. Therefore combinations with `n_frames=3` and both dimensions in `{11,12}` are explicitly rejected. The final override matrix classified 192 such calls and found no undeclared failures.

**Rejected alternative.** Dropping the depth-zero witness to permit those small combinations would reintroduce the main shortcut in exactly the cases most likely to dominate a compact curriculum.

## D5 — Use one analyzed semantic core

**Choice.** Route `self_check`, strict validation, observation, the Python mirror, rivals, witnesses, and lesson checks through common frame/marker analysis.

**Why.** Independent ad hoc parsers drift. The shared analysis verifies rectangular outlines, nesting/moats, one marker color, marker counts, and containment depths before any oracle or rival is evaluated.

**Failure handling.** Malformed grids return diagnostic errors from validators; oracle/rival entry points fail clearly rather than mutating or guessing.

## D6 — Four demonstrations and a six-position teaching schedule

**Choice.** Set `EXAMPLES_NEEDED = 4`; produce four demonstrations followed by one query from a six-position schedule whose windows contain the required witnesses.

**Why.** Individual labels were always correct, but correct examples alone did not teach the rule. Four demonstrations let every production window and every tested held-out rotation refute canvas-edge distance, constant one, and inside-any-frame without increasing scene complexity.

**Measured result.** The final census materialized 300 lessons (100 per band), 1,500 unique pairs, and all 1,500 query rotations with zero declared-rival ambiguity.

**Rejected alternative.** Two or three randomly ordered examples occasionally leave a query-divergent rival alive; relying on average witness frequency does not guarantee a complete lesson contains the witness.

## D7 — Correct the canonical-shortcut classification

**Prior choice.** An intermediate source declared `canvas_edge_distance_depth` in `CANONICAL_SHORTCUTS` because it fit the old generated stream.

**New choice.** Leave `CANONICAL_SHORTCUTS` empty and keep canvas-edge distance in `LESSON_COMPETITORS`/`SEMANTIC_RIVALS` only.

**Reason and evidence.** `workspace/probe_semantics.py` replayed every usable canonical pair and showed canvas-edge distance fails canonical training pair 3. A canonical shortcut must fit all canonical support, not merely the defective generated distribution. The final probe passes and is covered by a task-local regression.

## D8 — Retain a reusable declaration-consistency probe

**Choice.** Add `workspace/probe_semantics.py`.

**Why.** Future agents can source-bind a selected generator, enumerate declarations dynamically, verify canonical-shortcut fit, test rival survival, and report witness rates without reconstructing this review or copying rival names.

**Scope.** This is an authoring probe, not a universal theorem prover. Its finite samples and declared hypotheses must be reported as such.

## D9 — Leave audit targets unchanged

**Choice.** Do not repair `eed263bf30fc` or `90870ec1dd92` in this return.

**Why.** They were randomly assigned adversarial audits, and the duties explicitly separate audit findings from the selected task delta. Concrete source-bound evidence and proposed remedies are in `AUDIT.md`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-1d85d537b316e701:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c464c7b69ddbca31d8f58c27be9beeb4d4c15bf0f9ea0a70db3bb245bca429e9`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/df74e338b4f5/generator.py, unchanged SHA256 c464c7b69ddbca31d8f58c27be9beeb4d4c15bf0f9ea0a70db3bb245bca429e9. Explicit bounded no_issue:47portable tests plus120unique lawful source-bound generated probes (40perband), declared depth/witness conditions and3rivals refuted. Combined audit interrupted entering semantic stage,not passed. No owner probe execution, broader battery or undeclared-rival guarantee. Quoted basenames mean these exact target-local paths: `checks/audit/df74e338b4f5-combined.stdout` `checks/audit/df74e338b4f5-semantic-probe.exit` `checks/audit/df74e338b4f5-semantic-probe.json` `checks/audit/df74e338b4f5-semantic-probe.stdout` `checks/audit/df74e338b4f5-task-tests.exit` `checks/audit/df74e338b4f5-task-tests.stdout` `checks/audit/df74e338b4f5-task-tests/RUNTIME_MANIFEST.json` `checks/audit/df74e338b4f5-task-tests/checks/task_tests.xml` `checks/audit/df74e338b4f5-task-tests/progress.log` `checks/audit/df74e338b4f5-task-tests/result.json`

### Assessment or prior finding

## df74e338b4f5

**No issue found** in the checked source-bound scope. Audited generator SHA-256: `c464c7b69ddbca31d8f58c27be9beeb4d4c15bf0f9ea0a70db3bb245bca429e9`; declared rule hash `3ba84d8589ae`.

I inspected the frame parser, override realization, generated teaching contract, executable rivals/witnesses, six-position lesson schedule, and retained canvas-edge counterexample. The isolated portable task-test stage passed 47/47 tests (`checks/audit/df74e338b4f5-task-tests/result.json`). The source-bound probe then generated 40 inputs per band: all 120 were lawful and unique; every input exposed all declared depth/witness conditions; and none of `canvas_edge_distance_depth`, `constant_one`, or `inside_any_frame` survived (`checks/audit/df74e338b4f5-semantic-probe.json`).

The combined audit preset was interrupted while entering its semantic stage and is not counted as a pass; its stdout is retained at `checks/audit/df74e338b4f5-combined.stdout`. The clean conclusion rests only on the completed task-test and probe commands above. This is finite declared-rival evidence, not a proof against every possible shortcut, and the target was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## D10 — Native parametric recoloring-scope family (review-7444e31d07487847)

**Production source preserved.** `generator.py` remains byte-for-byte at SHA-256
`c464c7b69ddbca31d8f58c27be9beeb4d4c15bf0f9ea0a70db3bb245bca429e9`.
The default `recolor_scope=all_markers` program is the exact selected canonical
Racket text, SHA-256
`5cb8d0d25bfc546eb8551500c245c69cba7b50d9d8131a7a3e408475232152dc`.

**Alternative.** `recolor_scope=rarest_positive_depth` first detects the frames,
computes every marker's strict positive containment depth and its histogram,
selects the least frequent positive class with a deepest-class tie break, and
then recolors only markers in that class. Its exact Racket program SHA-256 is
`d89f7a000135b40caf56c0ecfe52d82934d06d004d71517763bd464b04611e35`.
Inputs are matched across settings.

**Teaching and range.** The adapter supports 2–6 demonstrations and 1–4 queries.
Every two-demo lesson distinguishes the two declared settings. The four-query
schedule contains landscape, portrait, 23×27, and substantive 30×30 cases; the
last case uses four nested frames, all containment depths, broadly spread
markers, and more than 250 frame cells. The first query is byte-identical between
one-query and four-query requests.

**Finite self-review.** The reusable
`workspace/parametric/audit.py` tool checked 18 matched-input jobs over seeds
0/17/97, demo counts 2/3/6, both settings, and four queries. Across 138 labeled
pairs, none of eight declared rivals survived the visible demonstrations and
every rival disagreed on at least one query. The rivals cover row-only and
column-only containment, constant/inside-any-depth shortcuts, deepest-only,
wrong tie direction, most-frequent selection, and incorrectly including depth
zero. This is finite declared-rival evidence, not a proof of unique induction.

**Protected execution and qualification.** All 138 authoring labels were replayed
in 204 protected-Racket evaluations. Native qualification covered both settings,
seeds 0 and 17, two demonstrations, and four queries in four jobs with 32
protected-Racket evaluations. The source inventory is
`workspace/parametric/evidence/manifest.json`; returned qualification evidence is
`checks/df74e338b4f5/qualification/`.

**Sequential dependency witness.** Step A computes the positive-depth histogram
and selected depth. Step B uses that selected depth to choose which markers to
recolor. On a qualified alternate-setting demonstration with histogram
`{1:4, 2:3}`, the correct intermediate is depth 2; a protected counterfactual
that forces depth 1 changes the final output. The reviewer-built and replayed
witness is `checks/df74e338b4f5/witness/witness.json`.

**Public projection.** Two saved three-demo/four-query challenges passed the
packet's public export checker. Public bytes contain only demonstration
input/output pairs and query inputs; identifiers are hashes of those visible
bytes and are invariant to private settings/programs/query answers.

**Status and limits.** Reviewer status is ready with owner exact-source acceptance
pending. No owner acceptance or training admission was performed. The input
grammar intentionally covers two to four nested rectangular frames and one
marker color, rather than every lawful canonical-looking scene.
