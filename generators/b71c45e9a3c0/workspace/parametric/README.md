# b71c45e9a3c0 native parametric family

`scope=all_objects` returns the exact selected canonical Racket bytes and
recolors every green object from the key above its bbox top-left corner.
`scope=largest_key_size` identifies the unique largest green object, reads that
object's bbox key as a target cell count, and recolors only the unique object of
that size using its own bbox key.

The matched sampler supports 2–6 demonstrations and 1–4 queries. The fourth
query is a boundary-spanning 30×30 scene with six differently sized objects.
`counterfactual-largest-size.rkt` replaces the largest object's key with its own
cell count and is retained only for the source-bound causal witness.

Run focused checks from the packet root with:

```bash
python3 review.py task-tests b71c45e9a3c0 --phase after --out ../checks/b71c45e9a3c0-tests
python3 review.py run python3 generators/b71c45e9a3c0/workspace/parametric/audit.py --out generators/b71c45e9a3c0/workspace/parametric/evidence/current/bounded-self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify b71c45e9a3c0 --out ../checks/b71c45e9a3c0/qualification --summary
```
