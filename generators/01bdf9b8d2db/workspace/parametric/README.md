# Native parametric family: `01bdf9b8d2db`

`finish=fill_all` is the selected canonical Racket source byte-for-byte.
`finish=mark_smallest_total` performs the same connected-chamber fill, counts
all filled cells by seed color, selects the least-total color with a lowest-color
tie break, and recolors every cell of that color to 9.

The two settings use identical inputs. The first two demonstrations are
constructive selector witnesses. The fourth query is a substantive 30×30 board.
`generate` supports 2–6 demonstrations and 1–4 queries with stable prefixes, so
the controller can reveal one private query per turn without exposing settings,
answers, future inputs, or total-count hints.

Sequential dependency: A is the canonical chamber flood; its intermediate is
the full cell-count histogram by seed color; B selects the least-total color and
recolors it. The retained wrong-intermediate counterfactual counts input seed
cells instead of flooded areas.
