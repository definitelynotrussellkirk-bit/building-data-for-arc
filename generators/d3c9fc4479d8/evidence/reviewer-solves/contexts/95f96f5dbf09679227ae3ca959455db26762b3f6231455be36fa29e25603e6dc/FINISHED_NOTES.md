# Post-repair visible-example solve log

This is a human-readable work log made after generator repair, so earlier rule
exposure is **yes**. During this solve phase I used only `solve/challenge.json`;
I did not consult the generator, Racket rule, reference solutions, or private
labels.

## Hypothesis 1

The first row is a color legend made of adjacent nonzero source/target pairs.
Scan it left to right: when two adjacent entries are both nonzero, record the
left color mapping to the right color and advance past both cells; otherwise
advance one cell. Remove the legend row and replace each body color once using
that mapping. Colors absent from the legend remain unchanged.

Visible evidence:

- Example 1 has `8→6` and `2→4`; body 8s and 2s change accordingly.
- Example 2 begins with zero and then has `3→5`, `5→6`; the output demonstrates
  one-step, simultaneous replacement (3 becomes 5, not 6), while 8 is kept.
- Example 3 has `9→4`, `8→5`, `1→3`; all three are applied and original 3 is
  preserved because it is not a source key.

I implemented this direct parser and one-step recoloring without a speculative
alternative because all three visible examples jointly distinguish the main
plausible errors: fixed-origin parsing, cascaded recoloring, and erasing
unmapped colors.
