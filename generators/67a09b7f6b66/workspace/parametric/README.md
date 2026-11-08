# Native parametric chamber-legend family

`legend_mapping=absolute_count` is the exact selected canonical Racket program:
each chamber's dot count (1, 2 or 3) selects that numbered legend entry.

`legend_mapping=anchor_cycle` adds an input-dependent composition. Exactly one
chamber has a dot at the upper-left interior corner. Step A identifies that
chamber and counts all of its dots. Step B treats the resulting count as the
cyclic origin of the legend: the anchor count maps to legend slot 1, the next
count to slot 2, and the remaining count to slot 3.

Inputs are matched across settings for a given seed and count request. The
adapter supports 2–6 demonstrations and 1–4 queries independently; generation
is prefix-stable. Its fourth query is an exact 30×30 extension with three
unequal-width chambers (8, 9 and 9 interior columns), which is lawful because
both Racket rules operate on connected zero regions rather than assuming equal
widths. Public turns reveal one query input at a time without settings, programs,
answers, future inputs or a total-query hint.

`audit.py` executes the two settings and five bounded rivals through protected
Racket. Its finite result is a teaching check, not a universal uniqueness proof.
