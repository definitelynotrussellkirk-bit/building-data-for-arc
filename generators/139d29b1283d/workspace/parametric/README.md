# 139d29b1283d native parametric family

`finish=intersection_only` returns the exact selected canonical Racket bytes.
`finish=overlap_size_payload` first derives the canonical in-bounds stamp
intersection, then uses its cell count to select the unique color-4 payload
component of that size and paints both in color 8.

The input sampler is setting-neutral and prefix-stable. It supports 2–6
independent demonstrations and 1–4 queries; the fourth query is a substantive
30×30 boundary-spanning case. `counterfactual-template-size.rkt` replaces the
input-derived overlap count with template size and is retained only for the
protected causal witness.

Run focused checks from the packet root with:

```bash
python3 review.py task-tests 139d29b1283d --phase after --out ../checks/139d29b1283d-tests
python3 review.py run python3 generators/139d29b1283d/workspace/parametric/audit.py --out ../checks/139d29b1283d/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 139d29b1283d --out ../checks/139d29b1283d/qualification --summary
```
