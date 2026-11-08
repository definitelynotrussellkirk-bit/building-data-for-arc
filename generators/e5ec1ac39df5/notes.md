# Working notes: e5ec1ac39df5

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## 2026-10-26 reviewer build

- Repaired the base validator/generator to accept the authoritative single-row and nonuniform-room cases, support off-center seeds, and make `grid_h`/`grid_w` strict observable controls.
- Added the task-local `target_rooms = seeded | neighbors` native family. `seeded` preserves the canonical rule; `neighbors` traverses color-7 room-graph edges from seeded rooms and paints the reached rooms' boundaries.
- Bounded checks: 7 focused tests, 400/400 ordinary source draws, protected authoring preflight for two settings/two seeds (32 Racket evaluations), causal witness replay, and four-query public-projection verification.
- Adversarial self-review repair: every visible minimum lesson gives the seeded room both a color-7-connected geometric neighbor and an unconnected geometric neighbor, preventing plain adjacency from matching the graph traversal.
- Current reviewer deliverable is source-bound and ready for owner replay. Owner qualification/acceptance and training admission remain pending by contract.
