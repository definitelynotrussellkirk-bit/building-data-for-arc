# Working notes: c1ee27b39d13

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric review — column ordering

**Choice.** Keep `column_order=source` as the exact canonical Racket bytes and add
`column_order=first_row_rank`. Stage A extracts the canonical submatrix selected
by the top-row color-4 and left-column color-5 markers. Stage B stably orders all
extracted columns by the values in the first extracted row.

**Teaching construction.** The first two demonstrations are constructively
separating: every extracted matrix distinguishes source order and first-row
ranking from reverse order, descending rank, last-row rank, second-row rank,
column-sum rank, row rank, and transpose. Inputs are identical between settings,
2–6 demonstration prefixes are stable, and four private queries are stored for
one-at-a-time reveal. The fourth query is a dense 30x30 scene touching all four
boundaries.

**Evidence.** Twenty focused tests passed, including twelve protected-Racket
labels. A 12-seed audit across demo counts 2, 3, and 6 covered 72 episodes and
found one declared survivor—the selected setting—in every case. Native
qualification passed both settings at seeds 0 and 17 (four jobs, 32 protected
Racket evaluations). The protected wrong-intermediate witness replaces the first
extracted row with the last as the sort key and changes the final matrix.

**Portability repair.** The pre-existing generator test used a fixed
`__file__.parents` depth and failed in the staged runtime. It now resolves the
library with `reviewer_support.find_root`, the canonical ledger with
`canonical_path`, and the base fixture from either documented data layout. The
portable task suite passes 26/26.

**Limit.** The rival set and seed sweep are finite. This is reviewer-ready
source, not owner-accepted or training-admitted.
