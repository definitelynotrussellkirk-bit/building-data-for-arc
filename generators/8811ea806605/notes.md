# Working notes: 8811ea806605

The approved production generator and exact canonical Racket rule remain the
authority for ordinary column gravity. The opt-in family under
`workspace/parametric/` adds line clearing in two orders: fall then clear complete
rows, or clear complete rows then fall. Clearing inserts empty rows at the top
and preserves shape. This is a state dependency: falling changes which rows are
complete; swapping the operations can change the final grid.

The native adapter, promotion contract and source inventory are complete.
Qualification passes all three modes at seeds 0 and 17 with three demonstrations
and four queries. Two wrong-order cases, at 5×5 and 30×30, have protected-Racket
intermediate values, final labels and native replay. Reviewer status is ready;
the owner must still freshly qualify and accept the exact integrated source.
No training admission is claimed. Canonical source and shared runtime are unchanged.

Teaching uses three mandatory demonstrations: several original full rows with
more full rows after gravity; an empty column that prevents any clearing; and a
different positive clearing count. This supports 3–6 demonstrations, centered on
three. Two demonstrations are deliberately rejected: retaining all three teaching
cases prevents constant-positive-count and positive-columns-only shortcuts without
weakening the four-query distribution. Queries are independent of demo count and
private setting and include substantive 5×5 and 30×30 cases.

Self-review found that seed 0 originally taught only interior full rows. A
Racket-executed rival that preserves full border rows matched all three demos
but produced 30 wrong cells on the 30×30 query. The first demo now constructively
includes both full border rows and one interior full row, preserving the 3/7
count distinction and the three-demo budget. The before/after source-bound
reproducer is `checks/8811ea806605/probe_border_shortcut.py`; its retained outputs
and three protected-Racket negative-rival regressions document the repair.

The composed modes also admit a histogram formulation: subtract the minimum
column count after falling, or subtract the original full-row count before
falling. The causal evidence establishes updated-state dependence rather than
irreducible simulation depth. A finite rival audit does not prove universal
identifiability or measured training benefit.

Current evidence: 46 focused tests pass. `workspace/parametric/evidence/manifest.json`
binds the executable prototype and compact reported evidence; the native
qualification/execution pair and causal witness are in the return's
`checks/8811ea806605/`. The reusable `audit.py` executed 566 protected-Racket
program/input evaluations, testing 37 named rivals on six retained three-demo,
four-query episodes and checking 12 independent count requests. No surviving
rival changes a retained query; before-clear caps of 3–6 rows remain harmless
survivors within the exercised grammar. The retained two-demo weak lesson shows
why a third demonstration is required. These are finite, source-bound results.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
