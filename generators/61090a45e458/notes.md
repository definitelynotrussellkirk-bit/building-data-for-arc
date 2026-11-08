# Working notes: 61090a45e458

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `91e10a278f8fc66c9e8a99b61d0c4a7ecd4c95cd57344703a52c4143b61d3e2b`.

# Design decisions for 61090a45e458

Final generator version: `2.0.0`
Final generator SHA-256: `91e10a278f8fc66c9e8a99b61d0c4a7ecd4c95cd57344703a52c4143b61d3e2b`
Canonical rule hash: `1041403d0f0a`

## D1 — Preserve the Racket authority; repair the curriculum generator

**Choice.** Keep the canonical Racket rule unchanged and pin it with `RULE_HASH`.

**Rationale.** Canonical inputs and outputs already express a coherent law: each frame contains a singleton seed and a larger target, and the target is recolored to the seed color. `rule_smoke` and `authority_sync` passed before any authority edit was needed. The defect was in distribution, metadata, validation, and teaching support, not in the rule.

**Alternative rejected.** Changing the Racket rule to encode the baseline generator's fixed positions would have canonized a shortcut and broken canonical authority.

**Failure mode controlled.** A future authority drift is caught by the hash pin and authority stages.

## D2 — Replace nine weak/inert axes with two exact observable controls

**Choice.** Advertise only `n_frames=1..3` and `target_size=2..5`, reject unknown keys and non-integer/out-of-range values, and recover both values through `observe_overrides`.

**Rationale.** The baseline declared grid and palette controls that were either unprobeable, single-valued, or not honored. Exact dimensions are emergent from frame geometry, so advertising `grid_h`/`grid_w` as exact controls would be misleading. Frame count and target size are semantically meaningful, independently observable, and constructively satisfiable across their full ranges.

**Alternatives rejected.** Keeping diagnostic-only fake axes would preserve surface variety without a falsifiable contract. Adding exact layout/palette axes was unnecessary for this repair and would enlarge the override matrix without improving the rule lesson.

**Probe.** Final override stage passed; task tests cover every `n_frames × target_size` pair and invalid/unknown override behavior.

## D3 — Use one canonical anchor plus two displaced-target profiles

**Choice.** Every consecutive three samples cycle through:

1. `canonical_top_left` — horizontal layout, target through the interior upper-left cell;
2. `shifted_bottom_right` — horizontal layout, target anchored away from that cell;
3. `shifted_vertical` — vertical frame layout with a center-displaced target.

`EXAMPLES_NEEDED=3`, and `lesson_identifiable` requires at least one demonstration that refutes `top_left_target_only`.

**Rationale.** Canonical demonstrations systematically support the rival “only recolor a target occupying the frame interior's upper-left cell.” Retaining one canonical anchor preserves source-task resemblance; two displaced counterexamples teach that location is irrelevant. A three-example deterministic cycle is cheap to audit and guarantees the witness in every consecutive lesson window.

**Alternatives rejected.** Pure random placement can accidentally produce all-canonical lessons. Removing canonical placement entirely would reduce fidelity. Two demonstrations would teach the chosen rival in ordered production, but arbitrary query rotation could hold out the sole counterexample; three profiles provide rotation-safe redundancy.

**Probe.** `shortcut_probe.py` checked 270 ordered lessons and all 810 rotations of their three scheduled examples; the shared census checked 300 production lessons and 1,200 query rotations. Both found zero ambiguities against the declared rival.

## D4 — Diversify geometry without changing the task law

**Choice.** Generate one to three separated frames, horizontal or vertical arrangements, multiple rectangular shapes, variable margins/gaps, and compact connected target shapes. Preserve exact canonical-size templates for two-frame horizontal samples.

**Rationale.** The baseline placed every frame on one row and used fixed interior positions, encouraging layout memorization. Geometry should vary while the local frame relation remains stable. Canonical templates ensure every difficulty band still hits the known size/palette support required by `profile_floor`.

**Alternatives rejected.** Arbitrary overlapping or nested frames would complicate parsing and introduce a new composition law. Disconnected targets were excluded because they create ambiguity about object identity and were unnecessary for canonical coverage.

**Failure modes controlled.** The parser rejects overlap, stray nonzero cells, malformed perimeters, ambiguous interior roles, disconnected targets, and ARC dimensions over 30×30.

## D5 — Make difficulty observable through target complexity

**Choice.** Default target sizes are easy 2–3, medium 3–4, hard 4–5. Explicit overrides retain full 2–5 support in every band.

**Rationale.** An intermediate implementation accepted `difficulty` but produced identical default distributions; strict `defect_lint` correctly caught the dead bands. Target size changes visual complexity without altering the rule or invalidating exact overrides.

**Alternative rejected.** Difficulty-specific frame counts would entangle two controls and make exact-axis evidence harder to interpret.

**Probe.** A failing regression was added first, then the band-aware sampler; final strict defect lint and all 50 task tests pass. The red/green evidence is retained under `checks/tdd-red-dead-bands/` and `checks/tdd-green-dead-bands/`.

## D6 — Keep role colors globally distinct

**Choice.** Each frame's border, seed, and target colors are globally distinct across the whole grid.

**Rationale.** This makes frame parsing and role observation unambiguous and prevents one frame's target from being mistaken for another frame's border or seed. The palette supports up to three frames because ARC provides nine non-background colors.

**Alternative rejected.** Reusing role colors across frames would increase palette variety but create avoidable global-component coupling. The rule itself does not require color reuse, and canonical support remains intact.

**Limitation.** This is a lawful but narrower input manifold than every conceivable instance of the abstract rule. The review does not claim completeness over reused-color variants.

## D7 — Use a structural validator rather than generation-history metadata

**Choice.** `self_check`, `strict_canonical_like`, and `observe_overrides` independently parse the grid: exact rectangular borders, separated rectangles, exactly one singleton and one connected 2–5-cell target per interior, shared target size, and no stray cells.

**Rationale.** A validator that trusts hidden generation metadata cannot protect against malformed inputs or future refactors. Structural recovery also makes exact overrides independently testable.

**Probe.** All canonical pairs are accepted and solved in task tests; malformed/ragged/stray-cell cases produce diagnostics.

## D8 — Declare the strongest known rival and make it executable

**Choice.** Register `top_left_target_only` in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; pair it with witness `target_not_top_left` and implement an executable lesson hook.

**Rationale.** Text-only claims do not let shared checks score lessons. The rival fits canonical evidence and has a small, lawful disagreement witness, making it the most useful concrete teaching adversary.

**Alternative rejected.** A weaker “always use upper-left color” heuristic does not precisely match all canonical transformations and is less diagnostic.

## D9 — Build a reusable probe for future agents

**Choice.** Add `workspace/shortcut_probe.py` plus tests and usage documentation.

**Capabilities.** It dynamically reads the generator's actual rival declarations, verifies canonical fit, finds a generated disagreement witness, checks consecutive production lessons, rotates each scheduled example into the query role, records source hashes, and supports `--assert-clean`.

**Rationale.** This closes the gap between a shared smoke summary and an exact replayable witness. It avoids hard-coding the rival-name list, so future edits cannot silently leave the tool stale.

**Probe.** The tool's own regression test was written red first and is included in the final 50-test suite.

## D10 — Testing and retained failures

The task-local suite contains 50 tests and covers canonical acceptance/solution, exact overrides, invalid overrides, all frame counts and target sizes, horizontal/vertical layouts, band behavior, canonical profile support, malformed inputs, the canonical shortcut, lesson windows, and query rotations. Genuine red iterations are retained under `checks/tdd-red*`; final task tests pass in both the working packet and a fresh patched extraction.

The full after battery passed all 12 stages with required rotation identifiability. The larger census materialized 300/300 lessons, 1,200 unique inputs, and 1,200 rotations with no materialization/scoring errors or declared-rival ambiguities.

## D11 — Self-review and remaining limits

The repair was checked for the new shortcut “profile or absolute position determines whether recoloring occurs.” The exact bottom-right witness shows the output still depends on seed/target roles rather than the profile, and every scheduled profile is solved by the same frame-local rule; the declared top-left rival is refuted in every tested lesson and rotation.

Remaining limits are explicit: finite rival checks do not prove unique induction; only connected 2–5-cell targets and globally distinct role colors are generated; the period-three profile schedule is deterministic; and the census does not enumerate every imaginable hypothesis. These are distribution boundaries, not hidden claims of universal coverage.

## 2026-10-25 native parametric reviewer build

Built a source-bound matched-input family under `workspace/parametric/` while
leaving the approved production generator and canonical authority unchanged.
The exact canonical default is `local_seed`.  The alternative
`largest_target_seed` parses all frames, computes each target size, selects the
uniquely largest target frame, and uses that frame's singleton seed color to
recolor every target.  The retained intermediate is the selected frame identity,
target size, and seed color; replacing it with the smallest-target frame changes
22 final cells in protected Racket.

The family supports 2–6 demonstrations and 1–4 prefix-stable queries, with four
distinct matched inputs and a substantive 30×30 query.  The bounded audit covered
160 episodes, 1,280 visible pairs, 4,000 finite declared-rival checks, 160 real
30×30 cases, 12 protected jobs and 41 unique protected-Racket evaluations with
no failures.  Native qualification passed 4/4 jobs for both settings on seeds 0
and 17 with 40 protected-Racket label executions.  The standardized witness and
replay are in `WORK/checks/61090a45e458/causal/`.

Reviewer status is `ready`; exact-source owner integration, fresh acceptance and
training admission were not performed.  Finite rival checks do not establish
universal identifiability or measured training gain.
