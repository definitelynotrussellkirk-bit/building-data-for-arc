# Bridge-routing native authoring family

`adapter.generate(seed, {"mode":"down"}, demos=2, queries=4)` emits a private
lesson. `up` reverses the destination endpoint, not the bridge construction.
The canonical rule is already genuinely sequential: bridges define cyan paths;
those paths determine token endpoints and counts. `wrong_order.rkt` packs tokens
on the unconnected strips before installing the same bridges.

From the packet's outer directory:

```sh
python3 review.py run python3 -m pytest generators/public_eval_2b83f449/tests -q
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_2b83f449 --root . --out ../checks/public_eval_2b83f449/preflight
python3 review.py run python3 generators/public_eval_2b83f449/workspace/parametric/audit.py --preflight ../checks/public_eval_2b83f449/preflight/preflight.json --out ../checks/public_eval_2b83f449/audit --seeds 32
python3 review.py run python3 ../check_public_exports.py ../checks/public_eval_2b83f449/audit/public --queries 1 --summary
```

The audit tool checks source binding, finite rivals, all pairs from two additional
6-demo episodes per setting through protected Racket, and an executed/replayed
wrong-order witness. Public files hash exact one-query visible bytes. Its private
presentation manifest shuffles the complete four-query bank before exposing any
prefix; query answers, programs, settings, future inputs and source indices never
appear in a public turn. Directory listings and bundle metadata are not public.
The negative public fixture deliberately leaks an answer and must be rejected.

Use fresh evidence output directories. Source changes require a new preflight.
The owner must still register the public lineage, review source, qualify natively,
and accept exact bytes. Authoring preflight is not owner qualification.
