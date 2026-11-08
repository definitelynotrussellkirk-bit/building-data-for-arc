# Working notes: e89e3ed7cb28

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Parametric family built in review-495aedda2e31ad59

The task-local family keeps the selected canonical bottommost-per-column program byte-exact as `output_mode=bottommost`.  Its nondefault `modal_survivor_color` setting first computes that canonical survivor grid, takes the unique modal nonzero survivor color, then filters the original input to that color.  The sampler makes the whole-input modal color a different decoy and places selected-color cells above nonselected column survivors, so raw frequency and “return stage A” shortcuts both fail.

The native contract supports 2–6 demonstrations and exactly four queries.  Every qualified episode includes distinct inputs and a substantive 30×30 query.  Focused tests, protected-Racket adversarial replay, authoring preflight, source-bound causal witness, and single-query projection checks are retained under `workspace/parametric/evidence/` and `checks/e89e3ed7cb28/`.  These are bounded reviewer checks only; owner source review, native qualification, acceptance, and any training admission remain pending.
