# Marker-count template rotation family

The canonical `identity` setting is byte-for-byte the selected ARC rule: find
the first separator-delimited template cell and stamp the complete template into
every zero-marked target cell.

The alternative `marker_count_rotation` setting adds a real sequential dependency:

1. **A — count markers:** count the zero cells inside the current target cell.
2. **Intermediate:** the count modulo four (0–3 quarter turns).
3. **B — choose and stamp:** rotate the complete template by that many clockwise
   quarter turns, then stamp it into the target.

Every input is legal under both settings and is sampled without consulting the
private setting. Each scene contains marker counts 1–4, a rotationally asymmetric
template, a literal template zero, unmarked distractor cells, and independent
2–6 demonstration / 1–4 query prefixes. The fourth query is an exact 30×30 board
with 5×5 logical cells, 20 targets, all four marker counts, and nonzero content
on every outer boundary.

`verify.py` executes both settings and five declared shortcuts through protected
Racket, checks public projection/privacy, and retains a wrong-intermediate causal
witness. This is reviewer evidence only; owner native qualification and exact-
source acceptance remain required, and no data is training-admitted.
