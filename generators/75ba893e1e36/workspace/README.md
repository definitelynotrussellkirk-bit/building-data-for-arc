# Authoring tools for 75ba893e1e36

The selected implementation is `../generator.py`; these tools are authoring
utilities or explicitly proposed variants. They do not supply selected training
labels or change approval. Canonical helpers expose answers, so keep them closed
during either solve that uses only visible examples.

| Tool | Purpose | Decisive evidence in this return |
| --- | --- | --- |
| `mutation_probe.py` | Run bounded generic shape mutations through input validation and actual canonical Racket; compare a separate task-specific rival. | `checks/mutation-lawfulness/linter-final-source/report.json` |
| `partial_override_probe.py` | Find a valid explicit completion of a rejected partial exact-control request. A failed bounded search is inconclusive. | `checks/partial-overrides/` |
| `parametric/prototype.py` | Proposed two-parameter episode generator, with one parameter choice shared by all demonstrations and queries. | `checks/parametric/bounded-six-v2/report.json` |
| `parametric/probe.py` | Materialize and label all six proposed settings with actual Racket; check their finite parameter rivals. | `checks/parametric/final-receipt.json` |

Run these from the outer packet using `python3 review.py run python3 generators/75ba893e1e36/workspace/TOOL.py ...`; payload paths are relative to
`WORK/repo`. Each tool documents its CLI. New outputs must use new evidence
paths. The task's portable `tests/` exercise the sampler and the reusable tools.

For the full isolated test collection (Python 3.12+, pytest, NumPy, Pillow and
Racket), use the packet's `review.py check --stage task_tests --phase after`.
Direct focused unittest entry points are also available. See `RESULTS.json` for
the actual interpreter, arguments, exit codes and final-source evidence.

The task patch contains no copied shared runtime. Reuse `reviewer_support` and
the public `arcpuzzles.Catalog` interface; do not import private per-puzzle
aliases or infer a runtime root from a fixed directory depth.
