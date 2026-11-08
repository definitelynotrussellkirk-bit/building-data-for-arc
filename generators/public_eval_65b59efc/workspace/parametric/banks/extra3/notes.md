# Current review decisions

- General rule: top panels define monochrome templates; middle panels are a permuted set of disjoint coarse masks keyed by those source colors; the bottom swatch under a top panel supplies that template's output color.
- Canonical `coarse_placement=identity` expands every mask cell at its original coarse coordinate. Alternate `transpose` swaps only coarse row/column placement and leaves micro-template orientation unchanged.
- The parser supports template sizes 3–5, three or four template columns, trailing separators, and blank right/bottom padding. Generated examples use asymmetric templates and masks, distinct swatches, and nontrivial color permutations.
- Sequential chain: A color-matches each mask to its template and aligned swatch; B expands those records into the output mosaic. The retained counterfactual matches by panel column instead of source color.
- The first two demonstrations reject the alternate setting and declared column, swatch, solid-tile, source-color, micro-transpose, fixed-template, and blank shortcuts.
- Finite rivals are bounded executable checks, not a universal uniqueness claim. Owner registration, exact-source review, qualification, acceptance, and training admission remain pending.
