# Working notes: 94549757a7f3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native cap / vertical-bridge family — review-ad1be2ac4da16d7d

Built a source-bound native family under `workspace/parametric/` without changing
`generator.py` or canonical authority. `finish_rule=cap_only` returns the exact
canonical Racket source. `finish_rule=cap_then_vertical_bridge` first creates the
canonical right caps, records exactly the input-zero coordinates newly changed to
color 2, then bridges zero cells between the first and last derived cap in each
eligible column. Stage B therefore cannot select columns before Stage A supplies
its input-dependent coordinate set.

A self-review found that five-column spacing could leave no zero gap between
neighboring runs, hiding the horizontal-bridge rival in a small query. Six-column
spacing fixes that teaching hole while preserving 2–4-cell runs. The final family
supports independently selected 2–6 demonstrations and 1–4 prefix-stable queries,
matched inputs, and a substantive 30x30 fourth query touching all boundaries.

The finite protected-Racket audit executes both settings plus eight semantic
shortcuts (skip Stage A, horizontal, first/last-only, full-height, green-endpoint,
wrong-color, and color-blind variants) across four seeds: 482 evaluations, and
only the selected rule survives the minimum two demonstrations. The portable task
suite passed 34 tests. Native qualification passed two settings at seeds 0 and 17
(40 protected labels), replayed byte-identically, and the skip-Stage-A witness
changes 104 final cells. Sixteen independent single-query public views verified.
This is reviewer-ready only; owner integration, fresh acceptance, and any training
decision remain pending.
