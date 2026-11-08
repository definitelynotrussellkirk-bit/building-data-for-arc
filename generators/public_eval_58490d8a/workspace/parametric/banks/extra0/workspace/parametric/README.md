# Native counting-board family

API: `program(settings)`, `generate(seed,settings,demos=3,queries=4)`, `public_turn(episode,index)`.
Only public_turn is model-visible. It emits train input/output pairs and one test input, stripping metadata and future queries. The controller must not publish directory/private receipts or full episodes.

From packet root:
```
python3 review.py run python3 generators/public_eval_58490d8a/workspace/parametric/audit.py --out ../checks/public_eval_58490d8a/new-audit --seeds 20
python3 review.py task-tests public_eval_58490d8a --phase after --timeout 180 --out ../checks/new-board-tests
```

Audit checks matched inputs, count boundaries, query-prefix identity, masking, executable rivals and Racket agreement. Source count metrics include repeated prefix requests; distinct_inputs counts independent scenes. Source changes require fresh preflight and witness replay. Canonical/default rendering retains original legend order, whereas the alternate ranks then accumulates actual object counts.
