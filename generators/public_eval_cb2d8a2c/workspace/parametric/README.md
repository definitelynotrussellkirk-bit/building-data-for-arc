# Count-controlled detours

Native API: `program(settings)`, `generate(seed, settings, demos, queries)`, and `public_turn(episode,index)`. Settings are exactly `{"trace_scope":"full_route"}` or `{"trace_scope":"longest_bypass"}`. Counts are independently 2–6 demonstrations and 1–4 queries. Full lessons materialize four; the public controller reveals one input at a time without a total-count hint.

`canonical.rkt` exactly copies the task's `reference.rkt`; `longest.rkt` changes the final selection scope. `model.py` contains constructive scenes, Python claims and independent rival predictions. Every native dependency is inside this folder; relocation is tested. The generator has literal `RULE_TASK_ID = 'ee_cb2d8a2c'` for owner registration.

From the packet outer directory:
```sh
python3 review.py run python3 -m pytest generators/public_eval_cb2d8a2c/tests --import-mode=importlib -q
python3 review.py run python3 generators/public_eval_cb2d8a2c/workspace/parametric/audit.py --out ../checks/public_eval_cb2d8a2c/new-audit --seeds 20
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_cb2d8a2c --root . --out ../checks/public_eval_cb2d8a2c/new-preflight
python3 review.py run python3 generators/public_eval_cb2d8a2c/workspace/parametric/audit.py --out ../checks/public_eval_cb2d8a2c/new-causal --preflight ../checks/public_eval_cb2d8a2c/new-preflight/preflight.json
```
Use new output paths and freeze executable sources before preflight. Labels returned by the sampler are claims, independently replayed through protected Racket. `audit.py` is a reusable same-task harness requiring only the adapter's documented hooks; it checks count requests, distinctness, matched inputs, prefix identity, private-field invariance, real rival execution and content-hashed public exports. The preflight-driven mode creates and replays a source-bound causal witness.

The module preserves fixed foreground roles: green source/path=3, red wall=2, blue count markers=1. Backgrounds vary. Only the controller should see private episodes, seeds, settings, source indices, programs and labels. Send the model a single `public/<hash>.json` file, not its directory listing or audit bundle.
