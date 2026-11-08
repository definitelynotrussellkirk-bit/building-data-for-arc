# Projection depth from the interior dot

This is a separate native parametric candidate for `d6607fc42bcc`; it does not
change the production generator or canonical authority.

`projection_depth=one` is the exact canonical Racket program: fill each notched
frame's interior and notch with its aligned dot color, then paint one full-width
row outside the opening. `projection_depth=dot_offset` first locates the dot and
computes its vertical distance from the notched edge, then paints that many
full-width exterior rows. The input-dependent distance is the intermediate that
controls the later projection operation.

The adapter accepts 2–6 demonstrations and 1–4 queries independently. Inputs are
identical across settings for the same seed/count request. The first two
constructive demonstrations distinguish both settings and six finite shortcuts;
the fourth query is a substantive 30×30 two-frame case. Public one-query turns
contain only the demonstrations and current query input.

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/d6607fc42bcc/tests/test_parametric.py

python3 review.py run python3 -m arcpuzzles parametric qualify d6607fc42bcc \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/d6607fc42bcc/qualification --summary
```

Qualification replays every label and finite setting rival through protected
Racket. Exact-source owner acceptance remains a separate post-integration step;
no data is training-admitted by these files.
