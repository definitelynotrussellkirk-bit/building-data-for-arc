# Vertical mirror plus selected-color horizontal completion

The default `completion=vertical` returns the exact canonical Racket program.
The alternate setting first completes the vertical mirror (A), counts colors in
that intermediate, then horizontally completes only its most frequent nonzero
color (B). The selected color and B's writes therefore depend on A's actual
input-derived result.

The teaching grammar alternates the selected color between the left and right
halves and makes its raw-input frequency rank alternate between second and
third within every three-demonstration episode. Those variations are
deliberate: always-left, always-right, always-rank-two, and always-rank-three
selectors all fail in a 200-seed / 600-pair shortcut audit. Inputs remain
shared across settings; 3–6 demonstrations and 1–4 queries are supported, with
the fourth query a substantive 30×30 scene.

This is reviewer-authored, source-bound prototype evidence only. Owner source
review, native qualification/acceptance, and any training admission remain
separate.
