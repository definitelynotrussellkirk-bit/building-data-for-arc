# Working notes: 938fbbaf1437

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## 2026-10-26 reviewer build

- Repaired the base generator so ordinary and overridden draws cover inset outer frames, two through four nested frames, isolated singletons, and strict advertised dimensions/counts.
- Added the task-local `counted_frames = all | squares` native family. `all` preserves the canonical rule; `squares` selects square frame components before per-cell containment counting.
- Bounded checks: 7 focused tests, 400/400 ordinary source draws, protected authoring preflight for two settings/two seeds (32 Racket evaluations), causal witness replay, and four-query public-projection verification.
- Adversarial self-review repair: visible minimum lessons now place the selected square proper frame at multiple nesting depths, preventing a fixed outer/middle/inner selector from matching all demonstrations.
- Current reviewer deliverable is source-bound and ready for owner replay. Owner qualification/acceptance and training admission remain pending by contract.
