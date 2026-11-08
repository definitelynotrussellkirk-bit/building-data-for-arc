# Optional canonical-label consistency gate — proposed

This authoring-only tool checks every stored labeled train/test pair for one exact
canonical task against actual execution of its selected Racket program. It reads
all variants, binds their exact program strings and ledger hashes, and uses
`reviewer_support.canonical_pairs(..., labeled_only=True)` for normalized pairs.
Only test pairs with no output key are skipped. Missing training labels, malformed
present labels, empty labeled sets, conflicting variant rules or labels for an
identical input, incomplete execution
receipts, and runtime errors fail explicitly.

The tool is a **proposal** under reviewer evidence, outside selected shared source.
It does not modify canonical labels, change reference authority, stage a runtime,
or approve a dataset or generator. A pass is a useful prerequisite for a future
Qwen9 data-admission workflow; other admission and teaching checks remain necessary.
Reports include reference programs and answer grids and must remain private
authoring evidence rather than model-visible challenges.

## Reproduce from the outer extracted packet

```bash
python3 review.py run ../.venv/bin/python ../checks/tool-proposal/canonical_labels/canonical_labels.py 623cca1dd5a8 --out ../checks/tool-proposal/canonical_labels/outline.report.json
python3 review.py run ../.venv/bin/python ../checks/tool-proposal/canonical_labels/canonical_labels.py a92bb76c10ef --out ../checks/tool-proposal/canonical_labels/counting.report.json
python3 review.py run ../.venv/bin/python -m pytest ../checks/tool-proposal/canonical_labels/test_canonical_labels.py -q
python3 review.py run ../.venv/bin/python ../checks/tool-proposal/canonical_labels/demonstrate_corruption.py --source-report ../checks/tool-proposal/canonical_labels/counting.report.json --out ../checks/tool-proposal/canonical_labels/intentional-negative.report.json
```

Output files must be new. The wrapper sets Racket and runs the payload from
`WORK/repo`; no Catalog staging/copy is involved. Python 3.12+, NumPy, Pillow, and
the included local runtime are required. `--root` explicitly selects another
self-contained repository/runtime, and `--expected-program-sha256` optionally pins
the reference. The default root comes from this tool's own path using
`reviewer_support.find_root`, never the caller's current directory or a predecessor.
Runtime source imports and ledger/generator source files must remain inside the
selected root. A missing generator is reported as absent, since label execution
does not depend on importing it.

The final command is an **intentional negative**, expected to exit **1**. It changes
one copied expected cell and reuses the actual Racket outputs retained by the
counting control. It does not change the ledger or claim a new Racket execution.
Both real canonical controls match all available labels; the synthetic negative
demonstrates a mismatch classification without inventing a natural source defect.

## Exit and report contract

| Exit | Meaning |
|---|---|
| 0 | Every labeled pair matched; at least one was checked. |
| 1 | One or more label mismatches, with exact input/expected/actual witnesses. |
| 2 | Data/binding/execution/output-format/report error; errors dominate mismatches. |

Every report includes the tool, canonical file, variant-row, selected generator
when present, executed program, and runtime source identities. Pair records retain
exact input, supplied label, and actual output plus their hashes. Shape-safe diffs
include missing and extra rows/columns; JSON `null` denotes a cell absent from one
grid, not ARC color zero. No dimension truncation or zip-only comparison is used.

## Reusable execution entry point

`execute_racket_batch(program, inputs, root=..., timeout=10.0)` returns raw Racket
outputs without requiring any trusted training label. It loads exact source with
public `ArcExecutor.step`; raw application deliberately uses
`_unwrap(executor._apply_rule(Grid(grid)))`, the same existing internal path used by
`arc_repl.isolated_verifier._worker`. This narrow internal coupling is explicit:
an incompatible runtime fails, rather than falling back to a Python interpreter.
The returned receipt binds the executed source hash and protected Racket identity.

The batch uses the existing pure-grid reference execution model. Inputs are copied
and checked for mutation. Failed inputs are retained without silent retry; a later
input gets a fresh, separately identified executor after an execution failure so lost rule bindings cannot
silently contaminate the rest. The reference parser rejects multiple outer forms.
This tool is a consistency check, not a hostile-code sandbox or a proof that an
arbitrary stateful reference has valid task semantics.

`compare_labeled_pairs(pairs, execution)` is the independent report/comparison
kernel. Unit tests inject fixed receipts to exercise normalization, variant
coverage, an explicitly intentional corrupted label, shape differences, error
precedence, invalid outputs, rule bindings, and path locality. They do not implement
a Python version of either ARC task. Actual Racket smokes are retained separately
in the reports and command logs beside this README.
