# Modal transform-composition family

`direct` is the byte-exact selected canonical rule. `modal_postcompose` keeps the
same template-and-marker reasoning but adds an episode-fixed composition rule:

1. Count marker colors 3–6 and select the unique repeated color.
2. Interpret that color as the global transform.
3. At every marker, apply the marker-local transform first and the global
   transform second, then stamp the normalized template in color 8.

Each scene has exactly five markers, all four local codes, one unique repeated
code, a connected full-D4-orbit template, and six disjoint 4×4 regions. Ordinary
seeds independently vary the template geometry, safe layout, and row-major marker
order while preserving the teaching constraints; inputs remain matched across
settings. The six demonstrations support stable 2–6 prefixes. The four queries
are distinct and end with a substantive 30×30 boundary case. Private settings,
programs, future queries, and query answers are excluded from each public turn.

The finite teaching audit covers direct and composed rules plus `global_only`,
reversed order, fixed-global, and first/last-marker shortcuts. The bounded sweep
covers both settings, 64 seeds, and demonstration counts 2, 3, and 6. Run from
the packet's outer extraction directory:

```bash
python3 review.py run python3 \
  generators/4296e507c770/workspace/parametric/verify.py \
  --out generators/4296e507c770/workspace/parametric/evidence/current
python3 review.py run python3 \
  generators/4296e507c770/workspace/parametric/sweep.py --seeds 64 \
  --out generators/4296e507c770/workspace/parametric/evidence/current/sweep.json
python3 review.py run python3 -m pytest \
  generators/4296e507c770/tests/test_parametric_modal_composition.py -q
```

This is reviewer evidence only: owner native qualification and exact-source
acceptance remain required, and no data is training-admitted.
