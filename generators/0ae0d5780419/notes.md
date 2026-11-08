# Working notes: 0ae0d5780419

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 — parametric admission review `review-35ba5091ff5939b8`

- Built an episode-fixed `match_policy` family: `first_exact` (the exact canonical program), `last_exact`, and `first_shape`.
- Kept the source task's real dependency: crop A/B, infer an input-dependent transform code, then apply that code to cropped C.
- The first demonstration has multiple exact matches and separates first from last; the second has only a recolored shape match and separates exact-color from shape matching. Additional examples cover unique exact matches, no-match identity fallback, padding/cropping, and large priority cases.
- Supports 2–6 demonstrations and 1–4 prefix-stable queries. The largest query is 30x29; width 30 is impossible for three equal-width panels plus two divider columns because total width is `3*n + 2`.
- Finite self-audit checked seven rival families for all three policies on seeds 0 and 17. No rival fit both teaching demonstrations while changing a query; this is not a universal uniqueness proof.
- Protected causal witness: a `last_exact` query has exact-match list `[2, 6]`; replacing the inferred code 6 with code 2 while leaving C and the application step unchanged changes 6 output cells.
- Native qualification passed all three settings on seeds 0 and 17. Reviewer status is ready; exact-source owner acceptance and training admission remain pending.
