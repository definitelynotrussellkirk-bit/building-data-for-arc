# Working notes: 761a24339019

## 2026-10-24 review

- Canonical repair: target markers now reserve the exemplar's complete translated color-3 footprint, and `self_check` rejects any clipped, overlapping, or input-overwriting stamp. The retained seed-6/sample-6 clipping witness is covered by `tests/test_generator_761a24339019.py`; production version is `2.0.2`.
- Parametric decision: keep the exact canonical Racket source as `stamp_transform=identity` and propose one episode-fixed alternative, `rotate_cw`, which rotates exemplar offsets 90° clockwise before stamping. Inputs are sampled independently of the hidden setting and are valid and output-distinguishing under both programs.
- Prototype: `workspace/parametric/prototype.py`, thin adapter `adapter.py`, and unapproved promotion contract `promotion.json`. It supports 2–6 demonstrations and 1–8 queries; the standard retained episodes use 3 demonstrations and 4 queries, while the first query is a substantive 30×30 boundary case.
- Evidence: `workspace/parametric/evidence/current/manifest.json` retains protected-Racket episodes for both settings, public redacted challenges, private labels/programs, demonstration-only rival elimination, and exact hashes. `workspace/parametric/evidence/manifest.json` inventories the source-bound prototype bundle.
- Limits: the variant is proposed only—neither variant approval nor training admission is claimed. Finite seeds establish bounded behavior, not completeness against arbitrary stamp programs.
- Next useful action: owner qualification should execute the adapter from a relocated checkout and decide whether to accept the two-setting family without changing the canonical default.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
