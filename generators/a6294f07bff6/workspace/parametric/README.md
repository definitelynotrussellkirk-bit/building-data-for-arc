# Native vertical flip with an input-derived cue axis

`canonical_ud` is the exact selected `(rule! flip-ud)` source. `cue_axis` adds
one singleton color-9 cue on exactly one non-corner border. Step A locates the
cue and derives the intermediate axis: a top/bottom cue means `ud`, while a
left/right cue means `lr`. Step B flips the whole grid along that derived axis.
Forcing the opposite axis changes the retained causal case.

The setting is fixed per episode. Both settings receive identical inputs built
before count slicing. The family supports 2–6 prefix-stable demonstrations and
1–4 prefix-stable queries, with opposite cue-axis cases in the first two demos,
varied rectangular dimensions and palettes, dense asymmetric content, boundary
contacts, and substantive 30x30 demo/query scenes. Public helpers reveal one
answer-masked query and hash only visible bytes.
