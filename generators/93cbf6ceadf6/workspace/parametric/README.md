# Parametric family: 93cbf6ceadf6

This family keeps the canonical first-stage inference and exposes one
second-stage episode-fixed choice:

- `output_transform`: return the normalized odd shape unchanged (canonical),
  rotate it clockwise, or flip it left-to-right.

The default `identity` program is the exact selected canonical Racket source.
Inputs never depend on the private setting. Every scene contains exactly three
separated objects: two share one translation-normalized shape and one has a
different shape. Repeated and odd controls have equal area and bounding-box
size; colors and reading-order roles vary; the odd shape is asymmetric under
all three declared transforms. Episodes have 2–6 demonstrations, exactly four
novel queries, and a substantive 30×30 edge-spanning final query.

The causal decomposition is A = compare normalized shapes and select the unique
odd object, then B = apply the episode's output transform to that input-derived
cropped grid. Replacing A with a repeated-object selection changes the final
output even when B is held at identity.
