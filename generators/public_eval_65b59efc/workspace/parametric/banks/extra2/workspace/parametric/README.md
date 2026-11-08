# Authoring replay

From the packet repository root:

```bash
python3 review.py run python3 -m pytest --import-mode=importlib generators/public_eval_65b59efc/tests -q
python3 review.py run python3 generators/public_eval_65b59efc/workspace/parametric/audit.py --out ../checks/public_eval_65b59efc/audit --seeds 0 1 2 3 4 5 6 7 17 43 --racket-seeds 0 17 43
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_65b59efc --root . --out ../checks/public_eval_65b59efc/preflight
python3 review.py run python3 generators/public_eval_65b59efc/workspace/parametric/audit.py --causal-preflight ../checks/public_eval_65b59efc/preflight/preflight.json --out ../checks/public_eval_65b59efc/causal
```

All outputs are unapproved reviewer evidence. They do not register, qualify,
accept, or admit the family for training.
