# Native 446ef5d2 family

`mode=assembly` is exactly the general canonical reference. `largest_region`
assembles first, then selects all maximum-area same-color pattern components
(border/background excluded) and recolors them to the L-marker color.

`generate(seed, settings, demos=2, queries=4)` supports independent 2–6 demos and
1–4 query prefixes. Ten source scenes are created; all four stored queries are
privately shuffled before prefix selection. `public_turn` emits only the visible
demonstrations and one current input. Never give an actor the full episode,
controller directory listing, certificate, program, setting or future query.

Native resources are self-contained. Rebuild the ordinary standalone copy after
editing core.py with `python build_generator.py`; `--check` is read-only.
Run source-bound checks from the packet outer folder:

```
python3 review.py task-tests public_eval_446ef5d2 --phase after --out ../checks/public_eval_446ef5d2-tests
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_446ef5d2 --root . --out ../checks/public_eval_446ef5d2/preflight
python3 review.py run python3 generators/public_eval_446ef5d2/workspace/parametric/verify.py --preflight ../checks/public_eval_446ef5d2/preflight/preflight.json --out ../checks/public_eval_446ef5d2/audit --seeds 32
```

Choose fresh output paths after source edits. verify.py checks current binding,
finite named rivals, count prefixes, public field invariance, six deliberate
corruptions, substantive 30x30 coverage, protected Racket parity, and a replayed
raw-fragment-area causal substitution. JSON evidence contains private answers.
It is not owner registration, native qualification, acceptance or training
admission. Author self-review is not an independent semantic review.
