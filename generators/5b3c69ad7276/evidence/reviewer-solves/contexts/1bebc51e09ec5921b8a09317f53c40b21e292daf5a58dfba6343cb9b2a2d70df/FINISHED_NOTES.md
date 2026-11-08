# Solve work log

## Exposure declaration

Before this solve I had not opened the Racket rule, generator implementation,
reference solutions, private query labels, or prior solution explanations for
`5b3c69ad7276`. I used only the prepared visible examples.

## Revision 0 — failing baseline

Hypothesis: the single nonzero cell is a seed. The output should preserve the
grid dimensions and paint the seed's entire row and entire column with the same
color, leaving every other cell unchanged. This explains all three examples,
including seeds on a corner and in the interior.

Planned probe: run the official visible-only checker against the untouched
`NotImplementedError` template first, establishing that the checker catches the
missing behavior before implementing the rule.

Alternatives considered: extending only toward selected edges, drawing a border,
or drawing just one axis. The interior example requires both full axes, while
the two corner examples show that the lines span the full grid rather than only
one direction from the seed.

Remaining uncertainty: the visible examples contain exactly one nonzero cell.
I will implement that stated visible domain and defensively return a copied grid
unchanged if no nonzero seed exists.

## Revision 1 — implement the cross

The failing baseline produced an execution error and passed 0/3 visible examples,
so the official checker is sensitive to the missing behavior. I implemented the
smallest rule matching the hypothesis: copy the grid, locate the first nonzero
seed, fill its complete row, then fill its complete column with the seed color.
The input is not mutated. No additional shape, palette, or direction behavior was
added.
