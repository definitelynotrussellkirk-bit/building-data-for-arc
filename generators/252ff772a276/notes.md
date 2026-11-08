# Working notes: 252ff772a276

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/252ff772a276/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->


## Native parametric handoff — review-9832cb58a9be5e67

Built `fill_scope=all_interior|winner_seed_rows`. The default program is byte-exact canonical; the alternative keeps canonical frame ranking, derives the selected winner frame's seed-bearing relative rows, and fills only those rows. Inputs are deterministic and setting-neutral for 2–6 demonstrations and 1–4 prefix-stable queries, with a substantive 30×30 fourth query.

Finite named-rival audit passed 96 sampled episodes. Native protected-Racket qualification passed 4 jobs / 40 evaluations. The source-bound wrong-intermediate witness substitutes the runner-up frame's row set on a qualified 30×30 input and changes 57 final cells. Owner acceptance and training admission remain unperformed.
