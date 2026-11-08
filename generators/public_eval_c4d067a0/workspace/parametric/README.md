# public_eval_c4d067a0: replayable authoring family

Settings: `completion=all|anchored_components`. The canonical/default program equals `../../reference.rkt`
exactly. No supplied grids or answers are read by the generator or adapter.

`generate(seed, settings, demos, queries)` accepts exact integers: demos 2..6 and
queries 1..4. Every episode retains `private_query_bank` of exactly four queries.
Call `presentation_order(presentation_seed)` independently of generation/query
ordinal and pass each returned index to `public_view`. Only those whitelisted
one-query views are model-visible. Never expose the raw episode, private index,
settings, program, future inputs, or answers. Do not enumerate the directory of
saved public turns to a model; reveal one selected file at a time.

From the packet root, use fresh output directories:

```sh
python3 review.py run python3 -m pytest generators/public_eval_c4d067a0/tests -q
python3 review.py run python3 generators/public_eval_c4d067a0/workspace/parametric/audit.py --out ../checks/public_eval_c4d067a0/audit-replay --seeds 0 1 2 3 4 5 6 7 17 43
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_c4d067a0 --root . --out ../checks/public_eval_c4d067a0/preflight-replay
python3 review.py run python3 generators/public_eval_c4d067a0/workspace/parametric/audit.py --out ../checks/public_eval_c4d067a0/causal-replay --causal-preflight ../checks/public_eval_c4d067a0/preflight-replay/preflight.json
```

`audit.py` independently executes protected Racket, tests demo-only rival
survival, checks query order/privacy invariance, and saves masked public examples
separately from the controller index. `--causal-preflight` verifies exact source
bindings and runs/replays the named wrong-intermediate counterfactual.

The original generator/adapter helpers are shared by exact-path aliases; Python
claims alone are not independent evidence. Protected Racket is the label authority.
The full native owner path is currently blocked by the bundled shared ID guard;
see `checks/OWNER_RUNTIME_BLOCKER.md`. Authoring preflight does not qualify or
approve source. A runtime edit invalidates the shared-runtime source binding and
requires fresh preflight and causal evidence.
