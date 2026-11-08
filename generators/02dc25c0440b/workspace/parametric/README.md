
# Parametric family: 02dc25c0440b

This family holds the sampled input fixed across settings and changes only the
right-side label semantics.

- `right_label=source_color` is the byte-exact selected canonical rule: reflect
  every nonzero left cell across the full-height color-9 guide.
- `right_label=visible_size` performs that mirror first, then recolors each
  right-side connected component with its visible cell count.

The minimum two demonstrations deliberately use different clipping regimes.
The first loses exactly one source cell; the second loses two or three. Across
the bounded seed audit, source/visible-size pairs included 3→2, 4→3, 6→4,
6→5, and 7→4. Thus neither a fixed clipped label nor “source size minus one”
can explain the minimum lesson set.

This gives a causal A→B witness: the correct second stage must inspect the
mirrored intermediate. The retained counterfactual labels mirrored cells by
the original source-object size, which differs whenever clipping removes one or
more cells.

The adapter emits deterministic Python claim labels. Independent qualification
re-executes all labels through protected Racket. Focused tests exercise the exact
canonical binding, matched inputs, 2/3/6 demonstrations, four queries, a 30×30
query, varied clipping loss, validation failures, shortcut rejection, and
protected-Racket parity. A bounded 128-seed audit additionally replayed 72 labels
through protected Racket.
