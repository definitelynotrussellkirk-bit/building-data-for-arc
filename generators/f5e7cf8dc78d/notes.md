# Working notes: f5e7cf8dc78d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric family

- The production generator and canonical ledger remain unchanged. The task-local native family is under `workspace/parametric/`.
- `frame_policy=all_bands` is byte-exact canonical. `frame_policy=leftmost_ranked` finds the unique leftmost singleton marker, converts it to its row-order rank, and paints side borders only for that selected band while preserving all marker rows and the canonical top/bottom closures.
- Inputs are matched across settings; 2–6 demonstrations and 1–4 prefix-stable queries are supported, with four distinct queries and a substantive 30×30 case.
- Adversarial self-review found two aliases in the first draft: the causal marker was always in absolute column 1 and the selected rank was tied to the visible profile. The final sampler varies both absolute marker column and rank across seeds, and retains executable `absolute_column_1` and `profile_rank` rivals.
- Current bounded evidence: 19 copied-runtime tests, 384 audited episodes, 384 exact 30×30 pairs, 0 declared-rival survivors, 4 protected-Racket qualification jobs / 40 evaluations, 16 sequential public views, and a protected wrong-rank witness.
- Evidence is under `checks/f5e7cf8dc78d/`; owner exact-byte integration, fresh qualification, acceptance, and explicit training admission are still required.
