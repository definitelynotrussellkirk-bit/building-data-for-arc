# Working notes: c7de5e8abc29

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 parametric proposal: diagonal versus orthogonal connection

**Decision.** Keep the exact canonical diagonal-connection Racket program as
`alignment=diagonal`; add the nearby `alignment=orthogonal` rule while preserving
same-color endpoint discovery and straight-line tracing. Every demonstration has
both diagonal directions plus horizontal and vertical pairs in disjoint zones, so
two demonstrations identify the episode-fixed setting without changing the core
reasoning. The adapter supports 2–6 demonstrations and exactly four private
queries; only one query input is exposed by `public_turn`.

**Boundary construction.** The fourth query is 30×30 and contains five diagonal
and four orthogonal endpoint pairs across all four edges. Depending on the fixed
rule, the output has 80 or 70 nonzero cells and reaches rows/columns 0 and 29.
During implementation, the first secondary diagonal lane accidentally received a
zero offset and duplicated the primary lane. The 30×30 regression exposed the
collision; lane offsets now alternate column and row shifts, and the regression is
retained in `tests/test_parametric_connector.py`.

**Evidence.** Nine focused tests pass. Protected Racket executed four all-setting
episodes (seeds 0 and 17; 28 labeled pairs), and the bounded adversarial report
also re-executed 12 minimum-lesson pairs while rejecting a corrupted label,
duplicate/missing queries, bad settings/counts, and public/private export
mutations. A final RED regression showed that equal first-turn public bytes with
different private records reached Python dictionary ordering and raised `TypeError`; the
writer now sorts by public ID only and reaches the intended duplicate-ID `ValueError`
before destination creation. See `workspace/parametric/evidence/manifest.json` and
`workspace/parametric/evidence/adversarial/report.json`.

**Status/limit.** Runnable source-bound prototype only. It is not qualified,
accepted, production-parametric, or admitted to training; owner qualification is
the next action. Canonical `generator.py` and canonical rule authority were not
changed.
