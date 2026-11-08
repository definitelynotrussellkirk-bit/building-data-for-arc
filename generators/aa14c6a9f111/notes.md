# Working notes: aa14c6a9f111

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## D1 — Add an anchor-area rectangle relay family without changing production

**Choice.** The task-local native family now has two matched-input settings: `all_outlines`, the byte-exact selected canonical program, and `anchor_area_fill`. The alternate reconstructs the three row-major rectangle records, measures the first rectangle's input-derived area `A`, selects rectangle `(A - 1) mod 3`, fills only that selected rectangle, and outlines the others.

**Sequential dependency.** Stage A must recover the ordered rectangles and anchor area before Stage B knows which rectangle receives a fill. The standardized protected-Racket witness uses a 30x30 nested scene with `A=900`, selecting index 2; replacing that intermediate with the canonical no-fill behavior changes 121 final cells.

**Teaching design.** The first two demonstrations vary anchor area, spatial order, palette order, sizes, and nesting so fixed-position, largest/smallest area or perimeter, color-order, all-filled, perimeter-index, and off-by-one modulo shortcuts cannot explain both settings. The same ten input profiles are used for both rules, with deterministic prefix-stable support for 2–6 demonstrations and 1–4 queries.

**Portability repair.** The inherited focused test used a fixed `Path.parents` depth and a single data layout. It now uses `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`, plus bounded ordinary/shared base-data candidates. The copied-runtime suite now passes instead of failing before collection.

**Evidence.** Final bounded audit: 18 setting/demo jobs, 60 visible pairs, 60 protected-Racket labels, 792 declared-rival checks, 24 public projections, 12/12 held-out setting disagreements, and three substantive 30x30 query banks. Native qualification passed all four setting/seed jobs for seeds 0 and 17; 16 one-query public views and the standardized witness replay passed. Copied-runtime task tests passed 15/15.

**Limits.** The evidence is finite and covers the declared three-rectangle grammar and named rivals. The production `generator.py`, canonical authority, and training state remain unchanged; exact-source owner acceptance is still required.
