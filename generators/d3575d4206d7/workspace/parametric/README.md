# Cyan lattice stamping, then rank newly painted components

This native family has one episode-fixed parameter:

| `finish` | Executed rule |
|---|---|
| `stamp_only` | Exact canonical source: use cyan panel masks and the demonstrated primary/fallback lattice rules to stamp new cyan cells. |
| `mark_largest_new_components` | Execute the canonical stamp first, isolate only cells newly changed to cyan, find their four-connected components, and recolor every maximum-size component red (2). |

The alternate rule is sequential. Stage B consumes the difference between the
original input and Stage A's canonical output; those newly painted components do
not exist before Stage A. The retained counterfactual instead ranks the original
cyan mask components and therefore changes the final output.

`adapter.py` loads the adjacent source-bound `prototype.py`. It supports 2–6
demonstrations and independently 1–4 queries. Inputs are matched across settings,
count prefixes are stable, and the first two demonstrations reject the other
setting plus six declared new-mask/component shortcuts. All generated scenes use
the production mixed lattice mechanism; no production-generator bytes change.

The query bank covers 17×17, 21×21, 23×23 and a substantive 30×30 case. The
largest case starts from the canonical 27×27 trailing-divider profile and extends
that already-uniform trailing border to 30×30. The panel lattice, canonical
semantics and protected-Racket result remain unchanged by the border extension.

From the packet outer directory:

```sh
python3 review.py task-tests d3575d4206d7 --phase after --out ../checks/d3575d4206d7-tests
python3 review.py run python3 generators/d3575d4206d7/workspace/parametric/self_audit.py --out generators/d3575d4206d7/workspace/parametric/evidence/current/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric manifest d3575d4206d7 \
  --evidence generators/d3575d4206d7/workspace/parametric/evidence/current \
  --include generators/d3575d4206d7/tests/test_parametric_new_cyan_components.py \
  --reported-checks '108 staged tests; 32-episode/320-pair finite-rival audit; 26 protected-Racket parity and causal evaluations; substantive 30x30 query'
python3 review.py run python3 -m arcpuzzles parametric qualify d3575d4206d7 \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/d3575d4206d7/qualification --summary
```

The evidence is finite reviewer qualification, not owner acceptance, universal
identifiability, measured training gain or training admission.
