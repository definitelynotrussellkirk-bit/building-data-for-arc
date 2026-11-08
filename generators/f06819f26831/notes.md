# Working notes: f06819f26831

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native completion-gain extension (2026-10-25)
Design: `completion_policy=all_copies|largest_gain`. Keep the exact canonical
greedy, coverage-ranked template completion. Measure newly filled original-zero
cells per resulting multicolor component; recolor the unique largest-gain object
cyan. A tie or no completion leaves the canonical result unchanged.
Rejected alternative: merely choosing the largest template drops partial-coverage
reasoning. The selected design compares different template sizes and original
partial counts, so neither largest template nor smallest partial is sufficient.
Plan: hand-derived and real-Racket regressions first; constructive unique-gain
scenes next; bounded executable rivals, export/count checks, native qualification
and a source-bound wrong-intermediate witness last. Existing production source
remains unchanged. The inherited mono-color-blob finding remains unresolved for
production: the native grammar explicitly treats such blobs as partial evidence
when their colors match a template; they are not advertised as inert distractors.

Native self-review completed: 20 new tests pass, including hand-derived sparse
versus dense partials, protected-Racket labels, all eight transformed literal
cases, immutable cached returns and tie behavior. No baseline tests existed
(the before command returned no-tests exit 5; it is not claimed as a green suite).
The retained authoring audit exercises 20 seeds and 800 setting/count requests,
5,200 repeated-prefix pairs (200 distinct inputs), 400 matched-input comparisons
and 2,000 masked public turns. 182 protected Racket evaluations eliminate every
listed rival on demonstrations alone. The large query has three templates and
twelve partial placements; original partial size, total finished size and newly
filled area are deliberately not equivalent. Only the last is the selection
metric. Earlier production audit remains needs_triage; no production repair or
training improvement is claimed. Owner exact-source acceptance is pending.

The isolated after-run initially failed two real-Racket tests: tests assumed
`shared/runtime`, whereas the frozen worker imports its hash-bound runtime from
the snapshot root. The tests and audit now use the snapshot root only when its
RUNTIME_MANIFEST exists; normal checkouts still use shared/runtime. The strict
same-checkout evaluator guard remains intact. The initial failing receipt and
its superseded qualification are retained; fresh final receipts follow the fix.
