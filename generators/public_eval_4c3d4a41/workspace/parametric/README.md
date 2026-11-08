# Insert a comb, then select a survivor

Native settings: `selection=insert` (exact canonical) and `selection=longest_survivor`. The latter consumes post-push/post-clipping lane counts. See ../../notes.md for grammar, source-rank shortcut repair and limitations.

From the outer packet directory:

```sh
python review.py run python -m pytest generators/public_eval_4c3d4a41/tests -q --import-mode=importlib
python review.py run python -m arcpuzzles.review_public_creation preflight public_eval_4c3d4a41 --root . --out ../checks/public_eval_4c3d4a41/preflight
python review.py run python generators/public_eval_4c3d4a41/workspace/parametric/audit.py --preflight ../checks/public_eval_4c3d4a41/preflight/preflight.json --out ../checks/public_eval_4c3d4a41/audit --seeds 32
```

Choose new output directories for reruns. The audit source-checks the preflight, compares declared rivals using only demonstrations, executes five rival programs through protected Racket, replays the fixed-rank teaching failure, executes/replays a wrong-order witness, and verifies private-field invariance and real public-checker rejection. `public_export.py` is reusable for exact one-query public batches; never hand the model the whole directory.

Preflight and these finite author checks are not owner qualification, acceptance, universal identifiability or training admission.
