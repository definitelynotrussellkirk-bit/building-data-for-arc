# Working notes: b570c79ec730

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 parametric prototype

- Added an **unaccepted task-local prototype** with episode-fixed `border_policy` values `preserve_existing` (the exact canonical Racket program) and `complete_bbox`. Both erase strict bbox-interior component cells; only whether missing perimeter cells are synthesized changes. Production source and canonical authority are unchanged.
- Every generated component is a connected thick notched rectangle with at least one missing non-corner bbox-edge cell. Thus every demonstration separates the canonical rule from the retained full-bbox-outline shortcut rather than allowing that shortcut to fit by accident.
- Inputs are setting-neutral; counts are independent at 2–6 demonstrations and 1–4 queries. Query four is a substantive 30×30 scene with at least 100 occupied cells, five colors, and content on all four boundaries. Public projection contains only demonstrations and the current query input.
- Fresh protected-Racket evidence covers both settings at seeds 0 and 17 with three demonstrations and four queries; every finite lesson has one survivor and all 28 labels match. Native qualification is source-bound but does **not** approve variants or admit training data.
- The issued root test `tests/test_generator_b570c79ec730.py` still hard-codes a staged canonical-data parent depth and fails before exercising the generator. It is frozen by the assignment and was not edited; the repair is to use `reviewer_support.find_root` / `canonical_path` when that test is next owned.
