# Blind solve notes — da16b5bf7632

I used only `solve-blind/challenge.json` and local Python reasoning. I did not
open the generator, canonical rule, reference outputs, prior solutions, or audit
records.

## Hypothesis

Each nonzero 4-connected component is a glyph. The output crops the glyphs,
top-aligns them, and concatenates them with one zero column between glyphs.
The ordering key is the number of enclosed zero regions (holes), descending;
components tied on hole count retain row-major order from the input.

Evidence from the visible examples:

- Example 2 has glyphs with 3, 2, 1, and 0 holes, and the output uses exactly
  that order.
- Example 3 has glyphs with 2, 1, and 0 holes.
- Example 1 has two one-hole frames followed by two zero-hole singleton glyphs;
  ties preserve their original reading order.

This explains the apparent size-order ambiguity: size correlates with hole count
in examples 2 and 3 but not in example 1.

## Implementation and test expectations

The solution extracts monochromatic 4-connected components, counts bounded
4-connected zero regions inside each crop, sorts by `(-holes, top, left)`, and
packs the unchanged crops horizontally. No intentional negative or diagnostic
revision was created; the first executable hypothesis is the genuine solve.
