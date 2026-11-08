# Working notes: af9ade3c3e16

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric review `review-47be421bacbfeadd`

Preserved the approved production generator byte-for-byte at
`7fdb17da0eaece92af735b304034b5a5e7694a2ee06e0d7fc0f20913fcaad2e1`.
Built the task-local native `finish` family under `workspace/parametric/`:
`frame_only` returns the exact canonical Racket bytes, while `center_cross`
uses the red-marker-selected hollow frame's derived bounding box to paint its
strict interior center row and column color 9 after the canonical cyan border
recolor. The wrong-intermediate witness keeps the selected border but derives
the cross from the outermost frame; protected replay changes eight final cells.

The sampler supports 2–6 demonstrations and four distinct controller queries,
keeps inputs identical across settings, and includes a substantive 30×30 query
with five frames and all four boundary contacts. The bounded self-audit passed
18 jobs (seeds 0, 17, 97; demo counts 2, 3, 6; both settings), rejected all
eight declared shortcuts using demonstrations only, and matched 147 protected
Racket labels. Native qualification passed four jobs and 32 protected-Racket
labels; 16 sequential public views, 24 first-turn invariance mutations and four
positive controls passed. Final focused tests passed 33/33. The existing
canonical test was also made portable through `reviewer_support` without
changing generator behavior.

Status is reviewer-ready only. Exact-source owner qualification/acceptance is
still required, and this work grants no training admission. The finite shortcut
set and bounded seeds do not prove universal identifiability.
