# Proposed prototype-rotation legend family

The canonical default matches each neutral target directly to the colored
prototype of the same normalized shape. This separate proposal adds one
episode-fixed alternative, `quarter_turn`: rotate each prototype clockwise,
then use the resulting shape-to-color legend.

Every sampled input contains all four orientations of one asymmetric L triomino
on both sides of the separator. Sampling is independent of the private setting;
only labels change. The legend order, colors, target positions, repetitions and
canvas sizes vary. Counts are 2–6 demonstrations and 1–4 queries. The fourth
query is a 30×30 stress scene with 65 separated targets, repeated orientations,
and nonzero content on every boundary.

Use `adapter.py:program(settings)` and `adapter.py:generate(seed, settings,
demos, queries)`. A sequential controller reveals
`prototype.visible_turn(episode, i)`, containing all demonstrations and only the
current query input. `verify.py` re-executes both admitted settings and three
finite shortcuts through protected Racket. The proposal is not canonical
approval, owner qualification, or training admission.
