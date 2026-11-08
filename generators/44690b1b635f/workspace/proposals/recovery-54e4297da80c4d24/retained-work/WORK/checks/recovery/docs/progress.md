# SDD ledger — plan: docs/superpowers/plans/2026-10-23-procedural-maze-diversity.md
Pre-flight: Task 1 produces the procedural profile consumed by Task 2 episode generation and Task 3 reporting; interfaces are named consistently.
Ruling: The original 350 MB packet cannot be rematerialized because the file service enforces a 100 MB hard limit. Use the exact current ARCpuzzles task source plus retained assignment/source hashes, build a source-bound recovery ZIP, and label official packet-only checks unavailable. Cost if wrong: maintainers must replay the patch in the original full packet before acceptance.
Ruling: No git metadata exists in this recovery workspace, so commits/worktree scripts cannot run. Preserve task boundaries and command evidence in this ledger and RESULTS.json instead.
Task 1: complete (tests: `PYTHONPATH=. pytest -q tests/test_role_topology_diversity.py` → 8 passed; compile: PASS).
Task 1: Evidence: forced procedural profile produced >=60/64 distinct normalized wall topologies in each band; default 800-draw census produced 59 total and 47 procedural topologies per band; fixed profiles and independent BFS oracle passed.
Task 2: complete (tests: `PYTHONPATH=. pytest -q tests/test_parametric_prototype.py tests/test_replay_tool.py` → 10 passed; compile: PASS; evidence hashes: PASS).
Task 2: Evidence: two retained 3-demo/4-query episodes, public/private split, exact program hashes, all rivals distinguished, all queries rival-sensitive. Racket execution remains explicitly pending the original packet runtime.
Task 2: Ruling: Use `neighbor_mode` and parity `phase` as proposed bounded parameters because both alter executed reasoning while preserving the canonical default. Cost if wrong: alternate variants may be unsuitable for training and must remain unapproved prototypes.
Task 3: complete as a recovery deliverable (62-file hash-bound WORK overlay, self-contained recovery repository, replay/sampling tools, reports, and evidence).
Task 3 verification: packaged-copy `PYTHONPATH=. pytest -q` -> 29 passed; complete manifest mock replay -> 62/62 destination hashes matched; second dry run -> 62 already-applied.
Task 3 boundary: official Racket-backed after battery, post-repair solve, allocation inspection, two audit targets, and `review.py package` remain pending the immutable packet.
