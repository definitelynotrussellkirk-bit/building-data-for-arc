# Native half-fill relay family

This directory contains the native parametric adapter for ARC task
`1a92a12bac06`.  The default setting, `half_only`, returns the exact canonical
Racket program: each separated red vertical bar has its bottom `floor(h/2)`
cells recolored cyan.

The alternative `largest_relay` setting adds a non-collapsing sequential rule:

1. **A — canonical half fill.** Recolor each bar's bottom half cyan.
2. **Intermediate.** Recompute four-connected cyan components. Newly cyan bar
   bottoms merge with pre-existing cyan bridge fragments.
3. **B — relay selection.** Select the unique largest post-fill cyan network
   and recolor every remaining red bar-top component cardinally touching that
   network yellow.

The sampler supports 2–6 demonstrations and 1–4 independent queries. It stores
four deterministic, distinct query inputs; `public_turn()` projects exactly one
unlabeled query at a time, with no hidden setting, program, answer, future input,
or total-count hint. The first turn is byte-identical between one-query and
four-query generation. Sizes range through a substantive 30×30 stress scene.

`audit.py` is the reusable bounded review tool. It executes selected rules and
plausible rivals in the protected Racket runtime, checks two-/three-/six-demo
teaching, emits all four one-query public turns, records boundary statistics,
and saves a wrong-intermediate causal case. Run it from the packet root:

```bash
python3 review.py run python3 \
  generators/1a92a12bac06/workspace/parametric/audit.py \
  --out generators/1a92a12bac06/workspace/parametric/evidence/current
```

The older `prototype.py` and its retained evidence are historical predecessor
work. `adapter.py`, `family.py`, `canonical.rkt`, `promotion.json`, and
`evidence/current/` are the current native proposal. Qualification and owner
acceptance remain separate gates; this directory alone does not admit training.
