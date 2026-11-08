# Native authoring and replay

`adapter.py` exports `program(settings)`, `generate(seed, settings, demos, queries)`
and `public_turn(episode, index)`. Supported settings are `transfer=one_hop`
(canonical) and `transfer=follow_chain`. Limits are 2–6 demos and 1–4 queries.
The full four-query bank is shuffled independently before prefix selection.

From the packet outer directory:

```sh
python3 review.py task-tests public_eval_d35bdbdc --phase after --out ../checks/wire-tests-new
python3 review.py run python3 generators/public_eval_d35bdbdc/workspace/parametric/build_generator.py --check
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_d35bdbdc --root . --out ../checks/wire-preflight-new
python3 review.py run python3 generators/public_eval_d35bdbdc/workspace/parametric/verify.py --preflight ../checks/wire-preflight-new/preflight.json --out ../checks/wire-audit-new --seeds 64
```

Outputs must be new. A source edit invalidates old receipts. The verifier checks
binding before/after work, finite shortcuts, independent count requests, protected
labels, single-query exports, negative export cases and causal replay. Its public
subdirectory is the only actor-facing material; the directory listing and all
other evidence are controller-private. Canonical bytes use the repository's
public serializer, not an ID including settings or future queries.

`replay_shortcut.py` reproduces the retained seed-57 gap and its repair from
`WORK/checks/public_eval_d35bdbdc/largest-two-regression`.

Authoring preflight and reviewer replay do not grant owner qualification,
acceptance or model-training admission.
