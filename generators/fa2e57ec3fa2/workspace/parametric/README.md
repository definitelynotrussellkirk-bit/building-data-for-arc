# Parametric rightward-ray family

`stop` is the exact selected rule: each color-2 emitter paints color 7 through
zero cells to its right until any obstacle or the edge. `mirror_turn` adds a
composed branch: the first-hit mirror supplies an intermediate direction
(color 6 turns up; color 8 turns down), then a second vertical ray consumes
that direction. Inputs are setting-independent, support 2–6 demonstrations and
four queries, and include a substantive 30×30 eight-emitter stress case.
