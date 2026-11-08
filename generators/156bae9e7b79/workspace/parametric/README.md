# Native parametric family: 156bae9e7b79

`postprocess=canonical` returns the exact selected keyed triangular projection.
`postprocess=highlight_projected_majority` first builds that projection, then
counts colors in the projected grid (excluding gray 5, cyan 8, and reserved 9)
and recolors the most frequent projected color to 9. Ties are resolved by the
lowest color, while the authored bank gives every retained scene a unique winner.

The sequential dependency is projection -> projected color counts -> recolor.
The retained counterfactual selects the majority from the unweighted key row
before projection; every authored scene makes that choice differ from the
projected majority. The bank supports 2–6 demonstrations and four distinct
queries, ending with a substantive 30×30 projection.

## Re-run the bounded audit

```bash
python generators/156bae9e7b79/workspace/parametric/audit_native.py \
  --seeds 64 \
  --out generators/156bae9e7b79/workspace/parametric/evidence/current-native/native-audit.json
```

The receipt checks deterministic paired episodes, stored labels, setting
separation, first-turn equivalence, the 30×30 boundary, and wrong-order
divergence. It is bounded evidence, not a universal uniqueness proof.
