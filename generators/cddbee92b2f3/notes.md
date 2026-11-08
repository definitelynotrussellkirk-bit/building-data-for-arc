# Working notes: cddbee92b2f3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 parametric proposal

- Kept the exact canonical left-to-right guide reflection as the default and
  added `source_side=right`. Inputs contain sources on both sides of the first
  full-height color-5 guide and are identical across settings.
- The adapter supports 2–6 demonstrations and exactly four distinct queries up
  to 30×30. Cases include multiple guides, occupied targets, clipping, and
  literal color-5 filtering; certificates reject “mirror both sides” and
  “move rather than copy.”
- The first export draft exposed all four query inputs together. A red regression
  led to a controller/public split: four controller-side queries, four opaque
  one-query public turns, no count/future-input hints, and byte-identical first
  turns for single-query and four-query use.
- Protected Racket checked both settings in the retained three-demo example and
  at the 2/6-demo boundaries. The retained export verifier checks hashes and
  projection, and rejected deliberate public-file corruption.
- Status remains **proposed prototype**: no owner qualification, acceptance, or
  training admission was requested.
