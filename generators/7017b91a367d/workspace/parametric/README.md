# Parametric family: overlap count map and triple-seeded flood

`overlap_policy` has two episode-fixed settings:

- `count_map` — exact canonical rule: overlay three aligned 5×5 panels and encode occupancy counts 0/1/2/3 as 0/2/4/8.
- `flood_from_triples` — first construct the count map, then flood from every 8 through four-neighbor 4/8 connectivity and promote reached 4 cells to 8.

The native adapter supports 2–6 demonstrations and 1–4 queries. Inputs are deterministic, prefix-stable, and identical across settings for the same request. The lawful source domain is fixed at a 5×17 three-panel input with a 5×5 output; the family deliberately does not fake a 30×30 case by padding.

Useful files:

- `adapter.py`: promotion interface.
- `prototype.py`: sampler, independent Python semantics, and finite teaching check.
- `canonical.rkt` / `flood-from-triples.rkt`: executable setting programs.
- `flood-through-singles.rkt`: wrong-intermediate causal counterfactual.
- `audit.py`: reusable boundary, determinism, named-rival, and optional protected-Racket audit.
- `promotion.json`: finite settings and request contract.

From the repository root, a future reviewer can rerun the bounded audit with protected Racket using the packet wrapper:

```sh
python3 ../run_with_racket.py python3 generators/7017b91a367d/workspace/parametric/audit.py --out ../checks/7017b91a367d-audit.json
```

The audit is finite evidence, not a proof of universal identifiability. Owner exact-source review and native acceptance remain separate.
