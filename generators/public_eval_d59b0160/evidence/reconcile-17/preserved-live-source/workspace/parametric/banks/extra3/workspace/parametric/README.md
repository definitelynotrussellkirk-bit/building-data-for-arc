# Portable color-key panel family

`adapter.py`, `engine.py`, and `canonical.rkt` are the native closure.
`promotion.json` declares exact setting and count limits. The default Racket
text equals the task's `reference.rkt` byte for byte. `build_generator.py` creates
the self-contained ordinary generator; `--check` detects drift.

After authoring preflight, run:

```sh
python3 review.py run python3 generators/public_eval_d59b0160/workspace/parametric/verify.py --preflight ../checks/public_eval_d59b0160/preflight-final/preflight.json --out ../checks/public_eval_d59b0160/new-audit --seeds 64
```

The auditor checks actual setting-program identity and current source, refuses
stale or changed preflight evidence, tests declared rival lessons, checks
independent request boundaries and matched settings, validates content-hashed
public turns and deliberate corruptions, and replays a protected counterfactual.
It is reusable for other task-local adapters exposing the same explicit API.
Shared `arcpuzzles.review_witness check --public-preflight ...` remains the
owner-compatible replay path; author receipts do not confer owner acceptance.
See ../../notes.md for grammar, semantics, retained findings and finite limits.
