# b13481ce1294 agreement-color XOR family

`all_exclusive` is the selected canonical Racket program byte-for-byte.
`agreement_color` first finds the unique same-color panel overlap, retains that
input-derived color, then emits only XOR-exclusive cells of that color. The
agreement color is therefore a selector consumed by the second step; replacing
it with the first different-overlap left color changes the final output.

Inputs are matched across settings, deterministic and prefix-stable, support
2–6 demonstrations and 1–4 private queries, and include a substantive 30×29
fourth query. Width 29 is the lawful maximum because equal side-by-side panels
plus one separator require odd total width. The first two demonstrations change
the anchor color, put a different overlap first in one scene, expose anchor
exclusives on both sides, and make a non-anchor color the most frequent exclusive,
refuting fixed-color, first-overlap, side-only and frequency shortcuts.
