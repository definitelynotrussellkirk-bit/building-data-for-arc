# Liquid-settling native authoring family

`adapter.generate(seed, {"mode":"settle"}, demos=3, queries=4)` returns a private
lesson with Python claim labels. Modes: `settle`, `largest_pool`. Default Racket
bytes equal `../../reference.rkt`. Never send this private object to a model.

From the packet outer directory:

```sh
python3 review.py run python3 -m pytest generators/public_eval_28a6681f/tests -q
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_28a6681f --root . --out ../checks/public_eval_28a6681f/preflight
python3 review.py run python3 generators/public_eval_28a6681f/workspace/parametric/audit.py --preflight ../checks/public_eval_28a6681f/preflight/preflight.json --out ../checks/public_eval_28a6681f/audit --seeds 32
python3 review.py run python3 ../check_public_exports.py ../checks/public_eval_28a6681f/audit/public --queries 1 --summary
```

Use new output directories after edits. `audit.py` checks exact preflight source
hashes, exercises a bounded seed/demo sweep, executes all 40 pairs from two extra
6-demo seeds through protected Racket, replays the retained teaching failure and
causal ablation, and writes shuffled, hash-named single-query views. The `negative/`
file deliberately leaks an answer and must fail the public checker. Only one
`public/<hash>.json` is model-visible. Directory listings, presentation manifest,
future queries, labels, programs, settings and evidence are controller-private.

The causal witness selects the largest source blob before settling, instead of
selecting the largest settled pool. Its final label differs on a preflight case.
The owner must register this public parent, review the source, then run native
qualification and acceptance. Authoring preflight is not a substitute.
