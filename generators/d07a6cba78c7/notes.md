# Working notes: d07a6cba78c7

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 parametric proposal

- Kept the exact canonical left-marker rule as the default and added a separate
  `marker_side=right` prototype. Every scene contains one left and one right
  magenta marker in different rows; settings share identical inputs, so labels
  must teach which marker selects the row.
- The adapter supports 2–6 demonstrations and exactly four distinct queries,
  including a 30×30 case. Equal-density, pairwise-distinct payload rows defeat
  fixed-row, densest-row, and “drop both borders” shortcuts.
- The first export draft exposed all four query inputs together. A red regression
  led to a controller/public split: four controller-side queries, four opaque
  one-query public turns, no count/future-input hints, and byte-identical first
  turns for single-query and four-query use.
- Protected Racket checked both settings in the retained three-demo example and
  at the 2/6-demo boundaries. The retained export verifier checks hashes and
  projection, and rejected deliberate public-file corruption.
- Author self-review found the fixed-first-row shortcut helper always cropped
  from the left. A failing regression now requires side-correct cropping; the
  teaching certificate was regenerated from the corrected rival.
- Status remains **proposed prototype**: no owner qualification, acceptance, or
  training admission was requested.
