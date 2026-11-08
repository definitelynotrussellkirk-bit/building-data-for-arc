# Beam-relay family

`adapter.generate(seed, {'finish':'trace_only'}, demos=3, queries=4)` returns a
private labelled episode. `highlight_deepest` changes only the finish; inputs
match for the same seed. `family.public_view(episode, index)` returns canonical
hashable bytes for exactly one visible query and its demonstrations. Never give
a model a private episode, evidence directory, or whole export listing.

Run from the outer review packet:

```sh
python3 review.py run python3 -m pytest --import-mode=importlib generators/public_eval_5961cc34/tests
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_5961cc34 --root . --out ../checks/beam-fresh-preflight
python3 review.py run python3 generators/public_eval_5961cc34/workspace/parametric/authoring.py audit --preflight ../checks/beam-fresh-preflight/preflight.json --out ../checks/beam-fresh-audit --census-seeds 64
python3 review.py run python3 generators/public_eval_5961cc34/workspace/parametric/authoring.py verify-export --bundle ../checks/beam-fresh-audit/preview
```

Choose fresh output paths. The audit checks current source/evidence hashes,
protected Racket labels, declared rivals, a protected counterfactual, deterministic
count prefixes, public projections and malformed export rejection. It reuses the
packet's witness validator/replayer and public-byte serializer; there are no
sibling-checkout or other-task imports. Source-bound receipts become stale after
any Python/Racket edit. Owner acceptance and training admission are separate.
