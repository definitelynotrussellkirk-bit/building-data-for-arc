# Authoring replay

From the packet repository root:

```bash
python3 review.py run python3 -m pytest --import-mode=importlib generators/public_eval_db0c5428/tests -q
python3 review.py run python3 generators/public_eval_db0c5428/workspace/parametric/audit.py --out ../checks/public_eval_db0c5428/audit --seeds 0 1 2 3 4 5 6 7 17 43 --racket-seeds 0 17 43
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_db0c5428 --root . --out ../checks/public_eval_db0c5428/preflight
python3 review.py run python3 generators/public_eval_db0c5428/workspace/parametric/audit.py --causal-preflight ../checks/public_eval_db0c5428/preflight/preflight.json --out ../checks/public_eval_db0c5428/causal
```

These commands create unapproved reviewer evidence only.
