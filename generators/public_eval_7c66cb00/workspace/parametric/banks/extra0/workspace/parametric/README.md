# Native band-sorting family

Use `program(settings)`, `generate(seed, settings, demos=3, queries=4)`, and `public_turn(episode,index)` from adapter.py. Public views whitelist train input/output and exactly the current query input. Never publish private episodes, audit/private, preflight, or witnesses.

From packet root:

```
python3 review.py run python3 generators/public_eval_7c66cb00/workspace/parametric/audit.py --out ../checks/public_eval_7c66cb00/new-audit --seeds 20
python3 review.py task-tests public_eval_7c66cb00 --phase after --timeout 180 --out ../checks/new-band-tests
```

Audit requests repeat scene prefixes; distinct_inputs is the independent-scene count. The copied audit implementation is task-local and has no predecessor imports. Changed source invalidates prior execution bindings and needs a fresh preflight and witness. Acceptance is an owner-only operation.
