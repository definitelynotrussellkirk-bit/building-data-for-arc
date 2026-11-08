# Parametric marker-selection family

- `marker_selection=all` is the selected canonical Racket program byte-for-byte.
- `marker_selection=template_width` measures the unique color-2 template's
  bounding-box width, adds five to obtain marker color 6–9, and stamps the
  normalized template only at markers of that derived color.

The input sampler is independent of the private setting. It supports 2–6
independent demonstrations and 1–4 prefix-stable queries; the intended training
shape is three demonstrations and four sequentially revealed queries. The first
pair of demonstrations distinguishes both settings and the finite rival set.
The fourth query is 30×30 with a dense 10×3 template and six markers distributed
across both halves and canvas boundaries.

Run focused checks from the packet outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/06b4c496c6cf/tests/test_parametric_06b4c496c6cf.py
python3 review.py run python3 \
  generators/06b4c496c6cf/workspace/parametric/audit.py \
  --out ../checks/06b4c496c6cf/self-review.json
python3 review.py run python3 -m arcpuzzles parametric qualify 06b4c496c6cf \
  --out ../checks/06b4c496c6cf/qualification --summary
```

Settings, programs and query labels are private. Public challenge bytes contain
only demonstration inputs/outputs and currently revealed query inputs.
