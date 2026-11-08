# Working notes: 733c1bac8c45

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review `review-11f3130ee717b04a` — 2026-10-24

Baseline generator 2.0.1 SHA-256: `9d7f8110731ec1cef657dd011a645c21a5aef56ad0cffda7ece24d0e67a17665`.
Repaired generator 3.0.0 SHA-256: `f26e0d57e48fd5913642f4d41bb15f9de6a02518c92131c20ecbdd15fc4e2a34`.
The canonical Racket rule is unchanged; `RULE_HASH` is `816c15c8ae9f`.

### Defect and repair

The issued generator had no task-local tests, no pinned rule hash, permissive legacy/unknown overrides, declared alias axes that did not form an honest observable contract, a weak validator, and no lesson-level rival/witness declarations. Its canonical examples are all five rows high with at most four active rows, so two wrong programs fit every stored label: process only the first five grid rows, or process only the first four active rows.

The repair replaces that contract with three literal public axes only: `grid_h` (4..12), `grid_w` (5..14), and `active_rows` (3..9). Known keys set to `None` follow the shared unset convention; unknown, retired, boolean, floating-point, and out-of-range values fail loudly. Incompatible explicit height/active-row requests raise a structured error naming both axes. The observer reports exactly those three visible properties.

The bounded teaching grammar uses zero background, three to nine active rows, one row-local nonzero color per active row, pairwise-distinct row colors, one to five cells per active row, variable row populations, visible movement in multiple rows, an internal gap, and multi-column travel. These constraints are teaching choices rather than claims about every mathematically lawful input to the Racket transformation.

### Curriculum decision

`LESSON_SCHEDULE_PERIOD = 4` cycles through two canonical-scale profiles and two taller profiles with more than four active rows. Therefore every three-demo/one-query rotation retains at least one tall counterexample. The declared canonical shortcuts are executable and are first verified to reproduce all four canonical labels; the tall profiles then refute both.

Seven witnesses target identity/right-pack, pattern translation without compaction, one-step movement, first-active-row-only, fixed-five-row, and first-four-active-rows alternatives. `lesson_identifiable` rejects a lesson when a named competitor matches all demonstrations but changes the query answer.
Malformed lesson records return explicit diagnostics before competitor evaluation, preventing missing-key crashes.

### Verification

- Task-local suite: 95/95 passed.
- Final source-bound stages: lint, selfcheck, rule_smoke, defect_lint, dist_gate, profile_floor, semantic_gate, diversity, override, grammar, racket_lint, and authority_sync all passed on generator SHA `f26e0d57…e2a34`.
- Strict semantic receipt: 4/4 canonical inputs accepted; 600/600 sampled inputs strict; all seven witnesses fired; all seven rival claims were checked; 12/12 complete lessons were identifiable; 0/48 held-out rotations were ambiguous.
- Reusable `workspace/probe_generator.py`: 1,024 unique generated inputs and 1,024 query rotations across all four bands/schedule positions, three override boundary cases, zero failures. It refuses a stale expected source hash and reports missing semantic declarations or schedule/profile drift.

### Limits

The Python mirror and workspace oracle are diagnostics; canonical Racket execution remains label authority. Finite success against seven named rivals is not a proof against every possible shortcut, and no model-training gain was measured. The pairwise-distinct row-color grammar intentionally excludes some lawful transformation inputs because this generator is designed as a teaching distribution, not as an exhaustive domain enumerator.
