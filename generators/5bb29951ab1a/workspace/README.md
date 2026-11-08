# Reviewer workspace for 5bb29951ab1a

`reference_probe.py` is independent review tooling, not label authority. It provides:

- `intended_output(grid)`: a frequency-role, original-input adjacency oracle;
- `corner_or_dense_output(grid)`: the strongest canonical-fitting rival found;
- `shortcut_witness()`: a small exact straight-bridge counterexample;
- `observed(grid)`: branch and witness counts recoverable from pixels;
- `racket_outputs(grids)`: a fail-closed portable execution of the selected canonical Racket source.

The focused tests import this helper through the task's `workspace/` directory. A useful manual probe from the packet root is:

```bash
python3 run_with_racket.py python3 -m pytest -q generators/5bb29951ab1a/tests/test_generator.py
```

The concrete Racket/rival disagreement is retained at `checks/shortcut-witness.json`; the baseline branch-coverage failure is retained at `checks/baseline-semantic-probe.json`.
