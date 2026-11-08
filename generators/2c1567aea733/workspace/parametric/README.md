# Native anchor-color family for `2c1567aea733`

This task-local family preserves the selected canonical rule byte-for-byte at
`anchor_color=1` and adds the matched-input alternatives `2` and `4`.

For every input, stage A groups foreground cells by color and reads the selected
anchor color's input-dependent top row. Stage B consumes that row to translate
every complete color vertically until all color tops match it. Columns, color
membership, disconnected pieces, shapes, and cell counts are preserved. Color
extents are horizontally disjoint, so the admitted grammar has no collision
priority or clipping ambiguity.

The native adapter supports 2–6 demonstrations and 1–4 independently truncated
queries. Six demonstrations and four queries are generated from separate fixed
pools, so changing either requested count cannot move the other split. The first
two demonstrations rotate all three colors through different vertical ranks,
refuting fixed highest/median/lowest/mean and identity shortcuts. The fourth
query is a true 30×30 boundary-spanning scene with three large irregular color
objects.

Run focused checks and qualification from the packet root:

```bash
python3 review.py task-tests 2c1567aea733 --phase after \
  --out ../checks/2c1567aea733-tests-v2
python3 review.py run python3 \
  generators/2c1567aea733/workspace/parametric/audit.py \
  --out ../checks/2c1567aea733/audit.json --seeds 16
python3 review.py run python3 -m arcpuzzles parametric qualify 2c1567aea733 \
  --out ../checks/2c1567aea733/qualification --summary
```

The family is reviewer-ready only. Exact-source owner acceptance and any later
training admission remain separate gates.
