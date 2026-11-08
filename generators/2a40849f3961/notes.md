# Working notes — 2a40849f3961

## 2026-10-06 — assignment review-4f4342b304636db9

The imported `2.0.1` generator filled almost the entire grid with color `5` and cleared one horizontal ten-cell corridor containing `1,2,3,4` in order. That sampler reduced the task to filling row gaps, used only one wall object, omitted the canonical rule hash, declared controls that were dead or overlapping, and did not resemble the canonical open-background mazes. The before battery retained under `checks/before/` reproduced those failures.

The selected Racket authority performs independent breadth-first searches for `1→2`, `2→3`, and `3→4` through non-`5` cells, with neighbor order up, down, left, right. It paints only zero-valued interior path cells `8`, leaves walls/checkpoints unchanged, and skips unreachable legs. The canonical examples include a disconnected leg, so `self_check` accepts such lawful inputs even though generated lessons deliberately keep all three legs reachable.

A concrete shortcut analysis found a stronger rival than “connect in a straight line”: change only the final two BFS priorities to up, down, right, left. That rival reproduces all five labeled canonical pairs, including the labeled test pair. The retained Racket-checked witness in `checks/shortcut-witness/` presents equal left/right shortest detours and changes 12 output cells. This is a finite rival, not a claim of universal identifiability.

Version `3.0.0` uses two profiles:

- `canonical_maze`: irregular open mazes with 4–5 separate barriers, including one source-scale long component; selected and right-before-left rules agree.
- `tie_break`: a symmetric obstacle forces equal left/right shortest routes for one leg; the selected authority takes the left branch and the retained rival takes the right branch. Decorative components keep the scene morphologically varied.

The ordinary schedule alternates profiles by `sample_index`. `EXAMPLES_NEEDED = 3`, so each four-pair lesson contains two witnesses and every one-query cyclic rotation retains at least one witness in the remaining three demonstrations. Honest observable controls are only height 11–13, width 12–14, and the two profile names. Unknown, mistyped, or out-of-domain overrides are rejected rather than silently ignored.

Task-local tests independently mirror both BFS orders, verify all canonical labels, exact override recovery, deterministic generation, malformed-input handling, morphology, witness behavior, lesson rotations, and Python/Racket parity. `workspace/reference_probe.py` adds a portable crossed override matrix, per-band sampling, canonical shortcut fit, and exhaustive cyclic lesson-start audit. The Python mirror is supplemental; retained `arcpuzzles apply`, authority, semantic, and battery evidence remains the source of authoritative Racket claims.

The selected solution-bank record's `target_code` contained comments absent from its `raw_code` and canonical authority. Execution parity already passed; this review set `target_code` exactly to the canonical/raw source, changing text only and not rule semantics. The canonical `puzzles.jsonl` file and canonical Racket authority were not edited.

Known domain limits: fixed role colors; fixed checkpoint order `1→2→3→4`; rectangular 11–13×12–14 grids; no generated unreachable legs; only straight wall components are constructed, though their combination creates irregular mazes; only the declared right-before-left tie rival is systematically refuted. No model-learning outcome or uniqueness against undeclared hypotheses is claimed.
## Current reviewer considerations

Source SHA-256: `a1d94459fe043258be0f7c8b7bdd4c54698c8ec08f18f433a61f02de59bdcae2`.

# Decisions — 2a40849f3961

Final generator: `repo/generators/2a40849f3961/generator.py`, version `3.0.0`, SHA-256 `a1d94459fe043258be0f7c8b7bdd4c54698c8ec08f18f433a61f02de59bdcae2`.

## G1 — Replace the one-row corridor, not merely widen it

**Observed baseline.** Version `2.0.1` filled the grid with walls and cleared a ten-cell horizontal corridor containing `1,2,3,4` in left-to-right order. The before battery reported one generated wall object versus a canonical median of 8.5, dead/overlapping controls, canonical-coverage drift, and an override contract with 1,585+ findings. The labels were technically compatible with the Racket rule, but the sampled lesson taught “fill the row gaps,” not pathfinding through open mazes.

**Choice.** Rebuild the sampler around zero-background mazes with multiple separate gray barriers, markers in distinct regions, route turns, and at least one detour. Generated labels remain wholly Racket-owned; no new transformation was added.

**Rejected alternatives.** Adding vertical corridors to the wall-filled template would still expose only narrow unique channels. Replaying canonical layouts would improve morphology but reduce novelty and risk memorization. Dense random walls produced too many disconnected or identity cases and made exact controls brittle.

**Failure controls.** Constructive placement is retried with bounded attempts; generated legs must all be reachable, output must change 5–60 cells, and self-check rejects malformed color/count/background cases. A regression test added after an intermediate defect-lint warning requires source-scale wall objects.

## G2 — Teach the strongest canonical-fitting tie rival explicitly

**Observed ambiguity.** The rule's BFS neighbor order is semantically observable only when equal shortest paths exist. Swapping left/right priority to `up, down, right, left` reproduces all five labeled canonical pairs. This is stronger than straight-line or nearest-marker shortcuts because it differs only on unresolved ties.

**Choice.** Add an explicit `tie_break` profile whose symmetric three-cell obstacle gives the `1→2` leg equal left/right shortest detours. The selected rule uses the left detour; the rival uses the right. Declare the rival in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `WITNESS_RIVALS`; expose the corresponding `left_right_tie` witness.

**Rejected alternatives.** Relying on random mazes to occasionally create a tie gives only frequency, not lesson-level coverage. Changing the Racket order or imposing a geometric tie rule would alter authority rather than repair teaching. Using an artificial metadata flag would not be observable from pixels.

**Evidence.** The exact Racket-checked witness is under `checks/shortcut-witness/`. `workspace/reference_probe.py` verifies the rival fits every canonical pair and that every generated tie profile refutes it.

## G3 — Use a two-profile alternating lesson schedule

**Choice.** Alternate `canonical_maze` and `tie_break` by `sample_index`; set `EXAMPLES_NEEDED = 3`. Every four-pair window therefore contains two of each profile. Under any one-query cyclic rotation, at least one tie witness remains among the three demonstrations.

**Why two profiles.** `canonical_maze` preserves irregular source-like morphology and avoids overfitting every sample to a symmetric teaching gadget. `tie_break` makes the authority's hidden ordering decision explicit. Alternation is deterministic, easy to audit, and independent of seed/difficulty.

**Rejected alternatives.** A probabilistic 50/50 mixture can produce all-witness-free demonstrations. Three or more profiles would require a larger demonstration count or a more complex coverage schedule without adding a known semantic distinction. Making every sample a tie witness would narrow morphology.

**Assembly policy.** Production is three demonstrations plus one query. Arbitrary query rotation is explicitly supported and tested, not inferred. The 100-lessons-per-band census materialized 300 lessons / 1,200 unique inputs and found no ambiguity against the declared rival in either production or 1,200 rotated queries.

## G4 — Advertise only controls recoverable from pixels

**Choice.** Keep exactly three axes:

- `grid_h`: integer 11–13;
- `grid_w`: integer 12–14;
- `scene_pattern`: `canonical_maze|tie_break`.

Every joint boundary combination is constructive. `observe_overrides` recovers all three exactly from the grid; unknown, mistyped, out-of-range, or wrong-type values fail loudly. `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty because the entire declared cross-product is supported.

**Rationale.** The imported generator advertised controls whose band-specific draw ranges contradicted their metadata and accepted an unknown key. Extra controls for wall count, marker locations, or detour length were not added because they are not reliably invertible from pixels and are unnecessary for the repair.

**Profiles and shape.** Canonical shape anchors `(11,12)`, `(12,12)`, and `(11,13)` are heavily weighted in every band while all nine advertised shapes remain possible. Difficulty changes weights only; it does not silently shrink the exact domain.

## G5 — Separate broad law validation from generated-domain constraints

**Choice.** `self_check` accepts canonical-lawful grids in a broad 5–30 envelope, including an unreachable checkpoint leg, because the authoritative rule skips such a leg. It requires rectangular integer grids, palette `0..5`, exactly one of each marker, at least one wall, zero as the modal background, and at least one reachable/output-changing leg. Generated inputs satisfy the narrower documented invariants: 11–13×12–14, 3–8 components, all legs reachable, and nontrivial output.

**Why.** Requiring all three legs reachable in the validator would reject an actual canonical example and confuse generated curriculum policy with rule semantics. Conversely, allowing identity or wall-free generated inputs would hide the operation.

## G6 — Synchronize selected authority text without changing semantics

**Observed baseline.** In `repo/shared/data/base/solutions/banks/f6c2fd26c5e5/H71__2a40849f3961.json`, `raw_code` already exactly matched canonical authority, while `target_code` added comments. The authority stage reported diagnostic text divergence but execution parity passed.

**Choice.** Set `target_code` byte-for-byte equal to `raw_code`/canonical source. The executable rule, normalized rule hash `cd7f3a44d341`, canonical puzzle file, and outputs are unchanged. This is a source synchronization, not a reference-rule modification.

## G7 — Add portable tests and a reusable independent probe

**Choice.** Add task-local tests under `tests/test_generator.py` and `workspace/reference_probe.py`. The tests independently implement both BFS orders, verify all canonical pairs, exercise every exact axis boundary across bands, test mutation/validation behavior, check morphology and deterministic replay, verify the four-pair schedule under every query rotation, and compare Python to live Racket when available. The portable wrapper executed all 58 tests with Racket.

The probe exhaustively crosses all 72 `(band,height,width,profile)` combinations, samples 100 draws in each production band, and checks 40 cyclic starts × 4 query positions × 3 bands. It is supplemental and labels itself as such; Racket apply/check evidence remains authoritative.

## Remaining limitations

The generator fixes colors and checkpoint order; generated scenes never include disconnected legs; barriers are composed from straight components; dimensions are deliberately source-scale; and only the declared right-before-left tie rival receives exhaustive lesson coverage. Finite tests do not prove unique induction against undeclared hypotheses or predict model learning. No unrelated shared runtime or audit-target source was changed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-09f3927e6ce094ad:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a1d94459fe043258be0f7c8b7bdd4c54698c8ec08f18f433a61f02de59bdcae2`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported on unchanged source a1d94459fe043258be0f7c8b7bdd4c54698c8ec08f18f433a61f02de59bdcae2. No issue found within the checked source-bound scope: 58 portable tests, a separately completed strict semantic gate, five canonical pairs, 72 override cross-products, 300 draws, explicit BFS tie witnesses and 480 query rotations pass. The combined audit controller was interrupted after tests; the later semantic receipt is separate, not a completed aggregate. This does not prove universal identifiability or resolve any other audit. Retain source-bound evidence: `checks/audit/2a40849f3961-combined/RUNTIME_MANIFEST.json` `checks/audit/2a40849f3961-combined/checks/2a40849f3961_audit_battery_summary.json` `checks/audit/2a40849f3961-combined/checks/2a40849f3961_audit_commands.jsonl` `checks/audit/2a40849f3961-combined/checks/2a40849f3961_audit_semantic_gate.log` `checks/audit/2a40849f3961-combined/checks/2a40849f3961_audit_summary.json` `checks/audit/2a40849f3961-combined/checks/task_tests.xml` `checks/audit/2a40849f3961-combined/progress.log` `checks/audit/2a40849f3961-combined/result.json` `checks/audit/2a40849f3961-semantic.launcher.exit` `checks/audit/2a40849f3961-semantic.launcher.log` `checks/audit/2a40849f3961-semantic/RUNTIME_MANIFEST.json` `checks/audit/2a40849f3961-semantic/checks/2a40849f3961_audit_battery_summary.json` `checks/audit/2a40849f3961-semantic/checks/2a40849f3961_audit_commands.jsonl` `checks/audit/2a40849f3961-semantic/checks/2a40849f3961_audit_semantic_gate.json` `checks/audit/2a40849f3961-semantic/checks/2a40849f3961_audit_semantic_gate.log` `checks/audit/2a40849f3961-semantic/checks/2a40849f3961_audit_semantic_gate.ok` `checks/audit/2a40849f3961-semantic/checks/2a40849f3961_audit_semantic_gate.receipt` `checks/audit/2a40849f3961-semantic/progress.log` `checks/audit/2a40849f3961-semantic/result.json` `checks/audit/2a40849f3961/reference-probe.exit` `checks/audit/2a40849f3961/reference-probe.json` `checks/audit/2a40849f3961/reference-probe.log`

### Assessment or prior finding

## 2a40849f3961

**No issue found in the checked scope.**  Audited generator SHA-256:
`a1d94459fe043258be0f7c8b7bdd4c54698c8ec08f18f433a61f02de59bdcae2`.
The source implements three shortest-path legs with the pinned up/down/left/right
BFS tie order and deliberately schedules tie witnesses for the canonical-fitting
right-before-left rival.

Checks performed:

- portable task tests: 58 passed, 0 failed/skipped
  (`checks/audit/2a40849f3961-combined/result.json`);
- strict audit semantic gate: pass
  (`checks/audit/2a40849f3961-semantic/result.json`);
- independent probe: 5/5 labeled canonical pairs match both the selected rule
  and the declared canonical-fitting rival; 72 exact override cross-products
  pass; 100 distinct draws per band pass self-check/oracle/replay; each band has
  50/100 explicit tie witnesses; and 480 one-query lesson rotations have no
  failures (`checks/audit/2a40849f3961/reference-probe.json`).

The combined audit preset itself was controller-interrupted after the 58 tests,
so I reran the missing semantic stage in a fresh source-bound runtime.  This is
not an approval and does not prove uniqueness against undeclared pathfinding
hypotheses, but I found no concrete shortcut, validator defect, or lesson
ambiguity in the inspected source and sampled domain.  The audit target was not
modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
