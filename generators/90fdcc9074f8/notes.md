# Working notes: 90fdcc9074f8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 — reviewer build `review-01a2cf183a5aabf8`

- The canonical base passed focused self-checks; no ordinary-generator source
  repair was needed.
- Added the exact-default `vote_policy=majority|unanimous` native family. Step A
  aggregates three panels into an input-dependent repaired mask; step B computes
  component-wise onion depth and crops the result.
- Initial alternate sampling could disconnect the unanimous mask. The sampler now
  chooses boundary omissions greedily only when the remaining unanimous core is
  still four-neighbor connected.
- Bounded audit covers seeds 0–127, all declared count corners and both settings;
  owner source review, native qualification and fresh acceptance remain required.
