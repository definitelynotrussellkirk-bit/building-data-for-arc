# Rectangle palette-scope parametric family

- `palette_scope=local` is the exact selected canonical Racket source.
- `palette_scope=largest_rectangle` identifies the unique largest gray rectangle, reads its ordered four-marker palette, and uses that input-dependent palette to fill every rectangle's quadrants.

Every generated scene has three separated rectangles. The selected largest rectangle is the middle row-major object, while the first object has the larger perimeter, so demonstrations reject first/last/perimeter shortcuts. Inputs are setting-neutral, deterministic, matched and prefix-stable. The four-query bank ends with a substantive 30×30 scene containing at least 100 gray cells.

From the repository root:

```bash
python -m pytest --import-mode=importlib -q generators/62757098b2dd/tests/test_parametric_palette_scope.py
python generators/62757098b2dd/workspace/parametric/audit.py \
  --out generators/62757098b2dd/workspace/parametric/evidence/current/self-audit.json
```

Protected Racket qualification and the source-bound causal witness remain the execution authorities.
