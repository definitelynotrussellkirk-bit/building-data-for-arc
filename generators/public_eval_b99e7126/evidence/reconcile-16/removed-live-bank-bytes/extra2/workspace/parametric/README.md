# Native tiled-completion authoring and replay

Settings: `completion=complete` (exact canonical default) or `fill_holes`.
The native folder contains all program, engine and generator resources.

From the outer packet directory, use new output directories:

```sh
python3 review.py task-tests public_eval_b99e7126 --phase after --out ../checks/tile-tests-new
python3 review.py run python3 generators/public_eval_b99e7126/workspace/parametric/build_generator.py --check
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_b99e7126 --root . --out ../checks/tile-preflight-new
python3 review.py run python3 generators/public_eval_b99e7126/workspace/parametric/verify.py --preflight ../checks/tile-preflight-new/preflight.json --out ../checks/tile-audit-new --seeds 64
```

The verifier rejects stale bindings, audits declared wrong rules, exercises
independent count boundaries, checks public/private isolation, uses the shared
canonical public-byte serializer, executes protected Racket, and builds and
replays the wrong-order causal witness. `public_io.py` is a standalone strict
checker for one-query files, duplicate JSON keys and content-hash identities.

Only individual files in the public subdirectory are actor-visible. Directory
listings, the entire bank, settings, recipes, gold outputs and all other receipts
are controller-private. Authoring preflight and reviewer replay do not grant
owner qualification, semantic acceptance or training admission.
