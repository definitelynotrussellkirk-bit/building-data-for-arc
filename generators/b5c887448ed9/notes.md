# Working notes: b5c887448ed9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric review — overwrite policy

- Added task-local `overwrite_policy=reading_order|longest_path_last`; the default returns the selected canonical Racket source byte-for-byte.
- The alternate constructs every canonical horizontal-then-vertical elbow, measures its input-dependent path length, then paints shortest-to-longest so the longest route wins crossings.
- Inputs are matched across settings and support 2–6 demonstrations plus four prefix-stable queries, ending in a substantive 30×30 case.
- A finite audit covered 12 episodes, 92 label claims, nine executable shortcut rules, 40 distinct protected-Racket executions, and 16 public views with no findings. This is bounded evidence, not a universal uniqueness proof.
- Native qualification passed both settings at seeds 0 and 17 with 3 demonstrations and 4 queries (40 protected-Racket evaluations). The source-bound wrong-order witness was replayed and changes the final output.
- Production `generator.py` and canonical authority were not changed. Owner exact-source integration, fresh native acceptance, and any training-admission decision remain pending.
