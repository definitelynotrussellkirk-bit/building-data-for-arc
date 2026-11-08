# Working notes: c2cd365ed4fa

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric extension

`workspace/parametric/adapter.py` preserves the canonical fixed-color histogram
program exactly and adds `column_order=count_ascending`. Eight-connected object
counts now select the column permutation; ties use the canonical color order.
The four-connected-order counterfactual retains correct bar heights while
changing column placement, providing a non-collapsing count-to-routing witness.

The retained seed-13 peer evidence identified a real lesson gap: demonstrations
without diagonal joins can fit a four-connected rival that fails on a query.
The separate adapter uses bounded constructive first-two demonstrations and
finite-rival rejection before queries are generated. It also teaches absent
columns, positive ties, maximum count six, and variable object areas. This
addresses the new adapter's lessons; the unchanged production sampler's
arbitrary demonstration prefixes retain their earlier limitation.

The adapter supports 2–6 demos and 1–8 independent queries (normally 3/4),
matched input streams across settings, and substantive 30×30 queries in an
explicitly extended input grammar. Production's 10–22 dimensional contract is
unchanged. Public IDs depend only on visible bytes; `turn_bytes` reveals one
query with no total-count hint. Programs and all query labels stay private.

Use the task's README and executable `verify.py` for reproduction. Native
qualification plus protected causal evidence are returned for exact-source
owner integration and acceptance. Current evidence is finite and reviewer-run;
no training admission or universal uniqueness is asserted.
