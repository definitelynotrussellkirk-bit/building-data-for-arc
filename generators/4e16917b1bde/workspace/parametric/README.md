# Depth-policy parametric family

This family keeps the selected divider-mirror grammar and changes only the
placement depth of the copied cells:

- `same_depth` is the exact canonical Racket program: a source cell at divider
  distance `d` is copied to distance `d` on the opposite side.
- `reverse_depth` first finds the divider and measures the input-dependent
  maximum source distance `M`; a source at distance `d` is then copied to
  distance `M + 1 - d` on the opposite side.

The alternate rule has a real sequential dependency: **A** locates the divider
and measures `M`; **B** cannot choose the target column until it receives `M`.
The first two demonstrations use opposite source sides, odd/even widths,
different divider colors, single/multicolor sources, and one near-divider gap.
They identify either setting without relying on those incidental features.

The adapter supports 2–6 demonstrations and 1–4 queries independently. The
four-query profile is 14×17, 18×21, 24×27, and a substantive 30×30 case.
`public_turn()` projects exactly one query input per turn, with no setting,
program, answer, future query, or total-count field.

Focused tests:

```bash
python3 review.py run python3 -m pytest \
  generators/4e16917b1bde/tests/test_parametric_depth_policy.py -q
```

Finite rival audit:

```bash
python3 review.py run python3 \
  generators/4e16917b1bde/workspace/parametric/audit.py \
  --out generators/4e16917b1bde/workspace/parametric/evidence/current/self-audit.json
```

Native qualification:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 4e16917b1bde \
  --out ../checks/4e16917b1bde/qualification --summary
```
