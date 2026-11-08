# Parametric family: fill, then select by filled area

`finish=fill_only` returns the exact selected canonical Racket source.  The
nearby `finish=highlight_largest_filled` rule first fills every per-color tight
bounding rectangle, measures the resulting solid components, and recolors the
unique largest complete component to color 9.

The constructor uses four sparse colors with a unique area winner.  Perimeter,
height, width, marker-count, color, and reading-order decoys are deliberately
separated.  Demonstration and query banks are deterministic prefixes; the four
query profiles are privately shuffled by seed and include one substantial
30x30 scene.  Inputs are identical across settings.

Sequential dependency:

- **A:** fill all color bounding rectangles.
- **Intermediate:** the filled grid plus the input-derived component-size table.
- **B:** recolor the unique largest filled component to 9.
- **Counterfactual:** selecting by filled-rectangle perimeter chooses a different
  component on the retained witness.

Useful commands from the repository root:

```bash
pytest -q generators/7f666a786bf3/workspace/parametric/tests/test_adapter.py
python3 generators/7f666a786bf3/workspace/parametric/audit.py \
  --out generators/7f666a786bf3/workspace/parametric/evidence/current/self-audit.json
python3 -m arcpuzzles parametric qualify 7f666a786bf3 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/7f666a786bf3/qualification --summary
```

The finite rival bank and sampled seeds do not establish universal uniqueness or
training benefit.  Exact-source owner acceptance remains separate.
