# Solve work log

## Exposure declaration

Before this visible-only solve was prepared, I had already inspected the assigned generator and its rule as part of the required repair lane. This solve is therefore exposed, not blind. During the solve itself I used only the displayed challenge and did not reopen the generator, Racket source, private query labels, or earlier solution explanations.

## Revision 1

The input is a 4×6 lattice of 3×3 symbols separated by all-zero rows and columns. Exactly one symbol is colored 8; its occupied-cell pattern appears to define the target shape. In each training example, every symbol with exactly the same 3×3 occupancy mask is recolored 8, regardless of its original color.

The new color 7 marks occupied cells of symbols lying strictly between aligned target-shape symbols. Example 0 emphasizes horizontal bridges, example 1 includes a vertical bridge, and example 2 combines horizontal and vertical effects. Empty cells and separator lines remain zero; unrelated symbols remain color 1. When an aligned interval passes through another matching symbol, matching-symbol status takes precedence and it stays color 8.

I implemented exact occupancy matching, all horizontal/vertical pairs of matches, and recoloring only the already occupied cells. The remaining uncertainty is limited to unseen malformed geometry; the displayed query uses the same 17×25 lattice contract as all demonstrations.
