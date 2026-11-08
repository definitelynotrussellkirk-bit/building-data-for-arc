# Repeated-measure edge sorting

`adapter.program(settings)` returns exact Racket text. `adapter.generate(seed,
settings, demos=3, queries=4)` returns private claims to be independently executed.
The only settings are `{"match_by":"occupied_area"}` and
`{"match_by":"bbox_area"}`; supported demonstrations are 2..6, queries exactly 4.

A: discover same-color eight-connected components and measure them.
Intermediate: each component, its measurement, and the frequency of that value.
B: translate to top if the frequency exceeds one, otherwise bottom. Keep columns.
The retained counterfactual replaces occupied-area measurements with box areas;
the changed group membership changes final vertical placements.

From the packet root:

```
python3 review.py run python3 generators/public_eval_62593bfd/workspace/parametric/audit.py --seeds 32 --out ../checks/public_eval_62593bfd/audit.json
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_62593bfd --root . --out ../checks/public_eval_62593bfd/preflight
python3 review.py task-tests public_eval_62593bfd --phase after --timeout 180 --out ../checks/public_eval_62593bfd-tests
```

Choose a fresh output after source changes. Deliver only individually projected,
content-hash-named public files to a model; evidence folders are controller-only.
The finite Python audit is not a substitute for protected-Racket label evidence.
