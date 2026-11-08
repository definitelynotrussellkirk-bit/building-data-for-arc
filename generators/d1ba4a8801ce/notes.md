# Working notes: d1ba4a8801ce

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Parametric prototype review-1235967f8e2a064a (2026-10-24)

Decision: keep the unapproved production generator and canonical rule authority untouched. Add a self-contained task-local sampler and adapter whose episode-fixed `shelf_axis` setting is `long` (the byte-identical canonical default) or `short`; both settings receive identical checkerboard/frame/loose-block inputs, and every generated frame is non-square so the labels distinguish the axes.

The adapter exposes independent 2–6 demonstration and 1–4 query counts. Retained episodes use four distinct queries, from 11×13 through a substantive 30×30 framed scene. `episode_io.py` supplies the same strict sequential public/private exporter used by the other two targets.

Evidence: `workspace/parametric/evidence/current/report.json` records 12 direct protected-worker jobs and 136 protected-Racket evaluations; `WORK/checks/final/independent-check.json` adds seeds 0–31, count-boundary, prefix-stability, shared-input, pairwise-distinction, and retained-bundle checks. The production source remains SHA-256 `93a8f0741b9a7b64aeb2093881da7716043644d1de8972491403d5544a3e6131`, rule hash `86c7183bd54d`.

Limit: production approval is false, so native qualification/acceptance was intentionally not claimed; status remains `not_accepted` and `training_admitted: false`. Next useful owner action is independent review of the production generator and prototype grammar before deciding whether approval and later exact-source qualification are appropriate.
