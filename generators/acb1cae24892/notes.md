# Working notes: acb1cae24892

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current reviewed state — 2026-10-25

The canonical rule remains unchanged byte-for-byte: every nonzero color appearing exactly twice defines the outline of its axis-aligned bounding rectangle, with same-row and same-column pairs as degenerate outlines. The base generator now exposes only three real controls (`grid_h`, `grid_w`, `n_colors`), honors them exactly across every difficulty band, rejects unknown and non-integer controls, reports observed values, validates canonical and generated inputs, mirrors the selected rule, and exposes `strict_canonical_like` for semantic review. Generated lessons cover row, column, and rectangle branches with one to three colors.

The canonical bank uses a legacy single-pair object for its `test` split. `workspace/parametric/preflight_compat.py` normalizes only that container shape to a one-element list and delegates every source, label, generation, protected-Racket, parametric, receipt, and source-change check to the official authoring preflight.

The native parametric family adds `finish_mode=fill_largest_hole`. Step A constructs the canonical outlines. Its input-dependent intermediate is the set of newly enclosed zero regions and their sizes/colors. Step B selects the largest such region and fills it with its surrounding outline color. The first two demonstrations swap which side contains the larger region, refuting fixed-side shortcuts. Four distinct queries include a substantive 30×30 case with two large disjoint enclosed regions. The canonical setting remains `outline_only`.

Current limits: demonstrations 2–6, queries 1–4. Qualification and owner acceptance are separate; this task-local source remains owner-pending until the exact integrated bytes are reviewed and accepted.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-254d83e902b42f90:v0001`. Disposition: **resolved**. Evidence basis: focused copied-runtime tests retained in `workspace/parametric/evidence/current/` and the packet check `checks/acb1cae24892-tests-final/result.json`.

Audited source SHA-256: `bf83c59e4414117256d70a9337cdf9d9f956ba821b138977fcb7960dc6b09fda`. The audited source differs from the current source; this assessment covers the reported defects and their direct regressions.

### Current decision

The inert advertised axes were removed; the remaining exact controls are implemented and observable across all bands; unknown keys and invalid scalar types are rejected; structural validation, a Python rule mirror, a pinned rule hash, portable task tests, and a semantic review hook were added. Regressions cover all joint boundary controls, all geometry branches, canonical labels, deterministic/fresh returns, malformed inputs, and the new parametric teaching contract.

### Prior finding

The former generator silently accepted unknown controls, ignored or difficulty-rejected much of its advertised exact-control surface, lacked observable overrides and task-local tests, and declared no semantic teaching contract.

This disposition records a bounded source repair. It does not imply universal correctness, owner acceptance, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
