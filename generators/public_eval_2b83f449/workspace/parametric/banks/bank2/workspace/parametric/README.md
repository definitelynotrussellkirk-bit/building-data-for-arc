# Gate-path flow family

`adapter.generate(seed, {'flow':'down'}, demos=3, queries=4)` returns a private
labelled episode. `flow='up'` changes only the endpoint selection; inputs match.
Use `family.public_view(episode, index)` for canonical bytes of one visible query.
Keep all source programs, settings, query answers, later queries and export
listings private. The separate presentation seed shuffles the complete bank;
select its first view for single-query evaluation without a total-count hint.

From the outer review packet:

```sh
python3 review.py run python3 -m pytest --import-mode=importlib generators/public_eval_2b83f449/tests
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_2b83f449 --root . --out ../checks/gates-fresh-preflight
python3 review.py run python3 generators/public_eval_2b83f449/workspace/parametric/authoring.py audit --preflight ../checks/gates-fresh-preflight/preflight.json --out ../checks/gates-fresh-audit --census-seeds 64
python3 review.py run python3 generators/public_eval_2b83f449/workspace/parametric/authoring.py verify-export --bundle ../checks/gates-fresh-audit/preview
```

Use fresh output paths. The retained authoring tool checks frozen source hashes,
all official labels (through preflight), additional protected labels, finite
rivals, a protected causal ablation, input-prefix stability, one-query privacy,
and malformed-export rejection. It is reusable with any family implementing its
small task-local hook API. The native adapter and sampler import only adjacent
resources and the standard library. No owner qualification or acceptance is
implied by these authoring checks.
