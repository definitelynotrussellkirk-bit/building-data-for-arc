# Feedback to Codex

## F1: Add a public-authoring sequential-witness command

**Symptom:** The native witness tooling is centered on already-qualified catalog tasks, while a new public-evaluation family has only an authoring preflight and is intentionally unregistered. This forced a task-local witness builder even though the required schema and protected evaluator already exist.

**Evidence:** `checks/tools/build_public_witness.py` binds an exact case from `checks/public_eval_b99e7126/preflight/preflight.json` or `checks/public_eval_a6f40cea/preflight/preflight.json`, executes correct and wrong-intermediate programs through protected Racket, writes the standard witness schema, and independently replays it.

**Suggested change:** Add `arcpuzzles.review_public_creation witness TASK --preflight ... --out ...` that selects an exact preflight case, verifies current source binding, emits the standard sequential witness, and performs replay. This would reduce duplicated security-sensitive orchestration while retaining the same owner gate.

## F2: Make bounded protected audits checkpointable

**Symptom:** The a6 family’s 32-seed protected audit exceeded the controller budget even though per-seed work was deterministic and earlier seeds had completed. The final source-bound run had to restart at a smaller 18-seed bound.

**Evidence:** `checks/public_eval_a6f40cea/audit/audit.json` records the completed 18-seed audit, including 36 episodes, 1,620 rival checks, 144 public views, and 60 protected evaluations. The b99 family completed the same audit shape at 32 seeds, showing that cost varies substantially by rule complexity.

**Suggested change:** Let the audit runner atomically checkpoint each seed with source hashes, support `--resume`, and optionally stop on `--max-seconds` while producing a valid explicitly bounded receipt. A resumed receipt should reject source drift and duplicate seed records.

## F3: Record immutable-label extension assumptions structurally

**Symptom:** A public parent can contain an apparent label convention or anomaly not uniquely supported by the remaining examples. Prose notes are necessary but difficult for owner reconciliation and later overlapping returns to compare mechanically.

**Evidence:** `public_eval_a6f40cea` requires an orientation-dependent checkerboard phase extension to reproduce all immutable labels; the assumption is documented in `repo/generators/public_eval_a6f40cea/notes.md` and covered by `test_documented_wide_stripe_phase_extension_matches_immutable_pair`.

**Suggested change:** Extend the public-creation inventory with an optional `inferred_extensions` list containing a stable ID, exact parent-pair locator/hash, concise assumption, alternatives considered, and covering test/evidence paths. Preflight should preserve this metadata without treating it as owner approval.
