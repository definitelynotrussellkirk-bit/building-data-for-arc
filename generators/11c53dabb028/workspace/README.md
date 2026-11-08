# Task-local review tools

The selected implementation is `../generator.py`. Workspace files do not select
or generate production labels.

| File | Purpose |
| --- | --- |
| `review_probe.py` | Reuse a hash-bound production lesson census, score all cyclic query roles against current rival declarations, measure defaults and joint overrides, and compare accepted grids with real Racket. |
| `REVIEW_PROBE_USAGE.md` | Commands, supported public APIs, evidence interpretation and bounded claims. |
| `check_lawful_mutations.py` | Execute `lawful_mutations.json` through public `Catalog.apply` and compare every expected output. |
| `lawful_mutations.json` | Thirteen lawful sparse/small/mutated grids that calibrate the generic mutation warnings. |
| `mutation_heuristic_notes.md` | Evidence and a scoped shared-tool proposal; no shared linter is modified. |
| `semantic_review_initial_failure.json` | Retained first probe failure and the six input grids of an actual query-rotation ambiguity. |
| `semantic_review_column_failure.log` | Focused failing regressions before actual column-major selection was corrected. |
| `semantic_review_intermediate*` | Clearly labeled earlier probe/command records, bound to the intermediate generator hash. |

The final successful probe and final command receipts are under the returned
packet's `checks/semantic-review-final*`, not the intermediate workspace files.
Exact evidence paths, optional gzip restoration and all command outcomes are
recorded in the root return. Use an environment with `numpy`, `Pillow` and
`pytest` installed outside the disabled Python user site for portable task tests.
