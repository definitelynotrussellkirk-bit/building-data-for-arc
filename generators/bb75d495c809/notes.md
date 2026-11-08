# Working notes: bb75d495c809

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 repair and parametric proposal

- Fixed the selected generator's public call contract: unsupported difficulty
  names and unknown override keys now fail before sampling instead of silently
  producing plausible data. The generation version was intentionally not bumped,
  preserving the existing seed-to-grid distribution for valid calls.
- Kept the exact canonical 4-connected size-recolor rule as the default and
  added a separate `connectivity=8` prototype. Every scene contains diagonal
  singleton–singleton and singleton–domino contacts, making the settings
  causally distinguishable on matched inputs.
- The adapter supports 2–6 demonstrations and exactly four distinct queries up
  to 30×30; large cases add real isolated component load rather than padding.
  Certificates reject cellwise-singleton and no-op shortcuts.
- The first export draft exposed all four query inputs together. A red regression
  led to a controller/public split: four controller-side queries, four opaque
  one-query public turns, no count/future-input hints, and byte-identical first
  turns for single-query and four-query use.
- Protected Racket checked both settings in the retained three-demo example and
  at the 2/6-demo boundaries. The retained export verifier checks hashes and
  projection, and rejected deliberate public-file corruption.
- The variant remains a **proposed prototype** with no owner qualification,
  acceptance, or training admission.
