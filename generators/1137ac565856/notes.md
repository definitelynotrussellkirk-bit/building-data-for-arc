# Working notes: 1137ac565856

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## D1 — Native frame-width relay (review-aba1370dbba2cbfe)

The exact smallest-enclosing-frame program remains the default. The alternate setting identifies the smallest complete frame strictly enclosing the red marker, maps its width 3/5/7 to selector 1/2/3, and uses that intermediate to select a remote payload. Every scene includes a smaller non-enclosing decoy frame, making the global-smallest counterfactual concrete and query-changing. The family supports 2–6 demonstrations, four prefix-stable queries, and a substantive 30x30 case.

The retained portable test now resolves canonical data through `reviewer_support.find_root` and `canonical_path`. A failing prototype run also exposed shuffled large payloads that could exceed their slots and a partial rival undefined on valid widths; the slots were made permutation-safe and the partial rival removed before final qualification. Source-bound evidence lives under `checks/1137ac565856/`; owner acceptance remains pending.
