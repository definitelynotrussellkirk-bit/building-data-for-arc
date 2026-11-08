# Reusable authoring tools

The selected implementation is `../generator.py`. None of these tools replaces
Racket labels or changes catalog/training approval. They expose reference
information and must not be consulted during a visible-only solve.

## Independent component ownership gate

`component_contract.py` is a standard-library-only, task-independent prototype.
It accepts one JSON grid and an explicit four-field role contract; a seed means
any cell not in the declared background or walls. Do not use this role model for
tasks containing additional distractor/object colors. The supplied
`component_contract.json` selects background 0, wall 5, cardinal connectivity,
and at most one seed cell per component.

From packet root, after restoring bundled evidence when necessary:

```sh
python3 repo/generators/6c8eefa043e1/workspace/component_contract.py --input checks/baseline-collision-input.json --contract repo/generators/6c8eefa043e1/workspace/component_contract.json --out checks/ownership-recheck.json
```

Exit **1** is the expected witnessed violation, not an execution failure. Exit 0
means only that this explicit contract is satisfied; exit 2 means bad input or
configuration. Reports contain exact input/tool hashes and deterministic
component anchors, sizes and seed coordinates. A competing-seed task can raise
the maximum or omit the gate; it must not be rejected under this task's policy.
`tests/test_component_contract.py` has 18 tests.

The optional shared change is to call this kind of independent measurement from
`shared/tools/generator_semantic_gate.py` under an explicit task declaration.
No shared runtime/tool edit is included or automatically selected. The prototype
is retained here so maintainers can evaluate it separately from source repair.

## Distribution and reference reconciliation

```sh
python3 run_with_racket.py python3 generators/6c8eefa043e1/workspace/review_probe.py --phase final --per-band 100 --seed 20261005 --out ../checks/new-domain.json
python3 run_with_racket.py python3 generators/6c8eefa043e1/workspace/validate_census.py --census ../checks/lesson-census.json --out ../checks/new-reconciliation.json
```

`review_probe.py` measures actual components and uses a separately written
sequential zero-flood oracle for checks only. `validate_census.py` compares this
oracle and the independent component gate with every saved Racket-labeled pair,
iterates actual rival declarations, and records simple shortcut/distribution
statistics. Neither tool claims universal induction or model accuracy gains.

## Audit reproducer

`audit_reproduce.py` extracts exact rotated-lesson witnesses from the two assigned
public census reports, demonstrates each declared rival's fit, replays the
actual query seed/index, and records the shadow generator's coercion defects.
Its `verify` mode reconciles subsequent `arcpuzzles apply` outputs and source
hashes. This tool is findings-only and does not edit either audited generator.

```sh
python3 run_with_racket.py python3 generators/6c8eefa043e1/workspace/audit_reproduce.py extract --out ../checks/audit
python3 run_with_racket.py python3 -m arcpuzzles apply dd038eb3d459 --input ../checks/audit/dd038eb3d459/input.json --out ../checks/audit/dd038eb3d459/racket.json
python3 run_with_racket.py python3 -m arcpuzzles apply e443791433ff --input ../checks/audit/e443791433ff/input.json --out ../checks/audit/e443791433ff/racket.json
python3 run_with_racket.py python3 generators/6c8eefa043e1/workspace/audit_reproduce.py verify --out ../checks/audit
```
