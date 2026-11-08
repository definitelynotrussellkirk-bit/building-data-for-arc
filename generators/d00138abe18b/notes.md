# Working notes: d00138abe18b

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 parametric proposal: row edge and row order

**Decision.** Preserve the exact canonical left-edge/top-down program as the
default and expose two episode-fixed parameters:
`read_side=left|right` and `row_order=top_down|bottom_up`. Each nonempty row is a
contiguous four-cell run `edge, interior, interior, edge` with three distinct
colors. Repeated edge values and nonmonotone row order make modal-row,
deduplication, sorting, opposite-edge, and reversed-order rivals disagree inside
the minimum two-example lesson.

**Boundary construction.** The fourth query is 30×30 with 24 nonempty rows,
including rows 0 and 29; runs include columns 0 and 29. The selected values form a
24×1 output. Demonstration count changes from 2 through 6 preserve the query set
and demonstration prefix exactly, and the controller retains four queries while
publishing only the current input.

**Evidence.** Eighteen focused task tests pass (ten new plus eight retained; the
retained suite still emits one pre-existing legacy-namespace warning).
Protected Racket executed eight all-setting episodes (seeds 0 and 17; 56 labeled
pairs), and the bounded adversarial report re-executed 24 minimum-lesson pairs and
passed count boundaries, corrupted-label/duplicate/missing-query rejection, and
public/private mutation checks. A final RED regression showed that equal
first-turn public bytes with different private records reached Python dictionary ordering
and raised `TypeError`; the writer now sorts by public ID only and reaches the intended
duplicate-ID `ValueError` before destination creation. See
`workspace/parametric/evidence/manifest.json` and
`workspace/parametric/evidence/adversarial/report.json`. The bounded semantic
pass found no defect; the later export self-review found and fixed the sorting defect above.

**Status/limit.** Runnable source-bound prototype only. It is not qualified,
accepted, production-parametric, or admitted to training; owner qualification is
the next action. Canonical `generator.py` and canonical rule authority were not
changed.
