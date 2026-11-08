# Native parametric family: 0005ab5b7704

`column_order` keeps the header-marker selector fixed while varying the second,
input-dependent ordering stage.

- `left_to_right` is the byte-exact canonical rule.
- `body_density_desc` first selects the yellow-marked columns, measures their
  nonzero body occupancy, then orders only that selected intermediate from
  densest to sparsest before packing the body.

Inputs are setting-neutral. Marked columns have distinct positive occupancies,
an unmarked high-density distractor makes marker selection necessary, and the
fourth query is a populated 30×30 stress case. The bounded audit checks declared
shortcut rivals, count/query prefixes, public first-turn stability, matched
inputs, and protected-Racket parity. Its finite scope is not a proof of universal
identifiability or owner acceptance.
