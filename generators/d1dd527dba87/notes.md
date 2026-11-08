# Working notes: d1dd527dba87

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 parametric prototype

- Added an **unaccepted task-local prototype** with episode-fixed `selector` values `largest` (the exact canonical Racket program) and `smallest`. Both preserve the normalized-XOR composition; only the component-selection step changes. Production source and canonical authority are unchanged.
- Each setting receives the same inputs. Every scene contains unique small and large components of colors 1 and 2, and the first three demonstrations reverse both row and column order. This directly defeats the reproduced bottommost/rightmost selection shortcut instead of merely documenting it.
- Counts are independent: 2–6 demonstrations and 1–4 queries. Query four is a substantive 30×30 scene. Public projection was checked structurally to contain demonstrations plus only the current query input, never settings, Racket, future queries, total-query hints, or query answers.
- Bounded adversarial work found that a byte-substring leakage test was itself ambiguous when a query output happened to equal a demonstrated output. The check now parses the public object and verifies that the query has no `output` field.
- Protected Racket execution covers both settings at seeds 0 and 17 with three demonstrations and four queries; every finite lesson has one survivor and all 28 labels match. Native owner qualification is unavailable while the production generator remains unapproved, so the protected worker receipt is retained instead.
- The issued root test `tests/test_generator_d1dd527dba87.py` still hard-codes a staged canonical-data parent depth and fails before exercising the generator. It is frozen by the assignment and was not edited; the repair is to use `reviewer_support.find_root` / `canonical_path` when that test is next owned.
