# Working notes: 7d09ccad28c8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Parametric family review — 2026-10-25

The base generator and canonical rule were retained. A copied-runtime portability
defect in the focused test was repaired by using `reviewer_support.find_root` and
`canonical_pairs` instead of a fixed parent depth.

The native family adds episode-fixed `route_mode` with `straight` as the exact
canonical/default program and `clockwise_elbow` as the composed alternative. Step
A casts each keyed ray to its input-dependent endpoint; step B turns clockwise at
that endpoint and casts a second leg. Demo/query streams are setting-independent,
independent, and prefix-stable for 2–6 demonstrations and 1–4 queries. The fourth
query is a substantive 30×30 four-frame case.

Retained evidence:

- 22/22 focused target tests passed.
- The source-local audit passed 12 seeds, 480 count/setting episodes, and 120
  full-bank pairs; every emitter-for-endpoint ablation disagreed.
- Authoring preflight passed original labels, ordinary generation at the required
  stages, both settings, four jobs, and 32 protected-Racket evaluations.
- The protected-Racket causal witness changes output when step B turns at the
  emitter rather than step A's endpoint.
- Public projection produced 16 independent one-query views; four first turns
  passed 24 private-field invariance checks and four positive controls.

This is reviewer-ready authoring evidence only. Exact-source owner review, native
qualification, fresh acceptance, and any training admission remain separate.
