# Visible-only solve work log

This is a human work log. I had earlier rule exposure from reviewing this generator, so this is not a blind solve. During this solve episode I consulted only the prepared visible examples and wrote a fresh implementation from them; I did not reopen the generator, Racket source, reference labels, or prior solution explanations.

## Revision 1 hypothesis
The four nonzero cells form a 2×2 source. Each source corner is copied as a 2×2 patch into the diagonally opposite quadrant, two and three cells away from the source block. The grid clips any part beyond an edge. The source block is preserved.

Evidence from the visible examples:
- Example 1 places the bottom-left source color in the upper-right patch and the top-right source color in the lower-left patch.
- Examples 0 and 2 show clipped one-column patches, so the rule clips per cell rather than dropping an incomplete 2×2 patch.
- All examples preserve the original four cells and leave unrelated background unchanged.

Implementation: find the first nonzero cell row-major as the source top-left, read the four source colors, then paint four bounded target patches while preserving nonzero cells.
