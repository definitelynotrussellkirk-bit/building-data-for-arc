# Native parametric family: finish after rectangle extraction

This directory contains the current native promotion candidate for
`c00a9bcded8e`.  It preserves the exact selected canonical Racket program as the
default and adds one episode-fixed, causally sequential alternative.

## Parameter

`finish` has two values:

- `colors_only` — canonical/default. Detect the qualifying near-solid
  rectangles, group them into spatial rows, sort each row left-to-right, and
  emit their colors. `canonical.rkt` is byte-for-byte the selected authority.
- `highlight_largest_rectangle` — perform the same complete extraction, then
  replace the output cell corresponding to the unique largest qualifying
  rectangle with color `9`.

The alternative has a genuine A→B dependency:

1. **A:** detect, measure, group, and spatially order all qualifying rectangles.
2. **Intermediate:** the row-major rectangle records, including each record's
   color, occupied-cell count, bounding box, and output position.
3. **B:** select the record with maximum occupied-cell count and recolor that
   record's output position.

A protected-Racket counterfactual uses the same intermediate shape but selects
by bounding-box perimeter. Generated lessons force the unique area winner and
unique perimeter winner to occupy different positions, so substituting that
wrong intermediate changes the final output.

## Episode grammar

The adapter supports 2–6 demonstrations and 1–4 queries independently. Both
settings receive identical inputs. Every scene contains 2–4 well-separated
spatial rows of exactly three qualifying rectangles plus isolated distractors.
The unique area winner moves across row/column positions and is constructed to
differ from the unique perimeter, height, width, color, first-position, and
last-position shortcuts. The retained four-query bank includes a substantive
30×30 case whose qualifying rectangles touch all four canvas boundaries.

## Files

- `adapter.py` — native generation contract, Python oracle, finite rival
  certificate, and dependency metadata.
- `promotion.json` — native adapter contract.
- `canonical.rkt` — byte-exact canonical/default program.
- `highlight_largest_rectangle.rkt` — admitted alternative program.
- `highlight_largest_perimeter.rkt` — non-admitted causal counterfactual.
- `audit.py` — reusable protected-Racket bounded audit for future reviewers.
- `evidence/current/self-audit.json` — current bounded authoring audit.

The previous `horizontal_read_direction` prototype remains in this directory as
historical evidence only. It is not the parameter declared by `promotion.json`.

## Retained checks and limits

The bounded self-audit covers seeds `0` and `17`, demo counts `2`, `3`, and `6`,
all four queries, both settings, matched inputs, prefix consistency, 30×30
boundary stress, eleven declared hypotheses, and 93 protected-Racket labels.
The portable source-bound task suite and the focused parametric tests are kept
separately in the packet checks/evidence.

These are finite deterministic checks. They do not prove universal
identifiability, measured learning benefit, owner acceptance, or training
admission. Public projections must be produced through the shared exporter so
settings, programs, seeds, source indices, future queries, and answers remain
private.
