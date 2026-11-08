# Working notes: e0ef0cfeaf88

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 repair and parametric review

- Reproduced the retained hard-band canonical-profile miss (0/20). Replaced the
  independent 8% coin flip with a deterministic 1-in-12 schedule that rotates
  through all four canonical forms. The pinned census now has exact support in
  every band while the 500-draw prior remains near 8% and diverse.
- Built `workspace/parametric/` with `extent=edge|two_steps`. `edge` is copied
  byte-for-byte from the selected Catalog authority; the compact solution-bank
  rendering was rejected because it is semantically equivalent but byte-different.
- Inputs are setting-independent and leave at least three legal continuation
  cells beyond each tail, so every demonstration distinguishes edge-reaching
  rays from two-cell rays. Supports 2–6 demonstrations and four prefix-stable
  queries; the last is a 30×30 four-tail scene whose canonical output contacts
  all four boundaries.
- Protected-Racket evidence covers both settings, demo-only finite-survivor
  teaching, exact labels, strict controls, and public/private projection.
- Prototype remains proposed only: no owner acceptance or training admission.
