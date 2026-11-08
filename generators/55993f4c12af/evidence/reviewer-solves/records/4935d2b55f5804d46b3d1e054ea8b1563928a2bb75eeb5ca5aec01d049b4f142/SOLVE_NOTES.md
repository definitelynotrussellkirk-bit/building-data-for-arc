# Solve work log

## Exposure declaration

I had already inspected the repaired generator while reviewing it, so this is an
**exposed** solve, not a blind measurement. During this solve episode I used only
`solve/challenge.json`; I did not reopen the generator, Racket rule, reference
solutions, earlier solve explanations, or private labels.

## Revision 1

The three visible inputs all have even height and naturally split into equal top
and bottom panels. The visible outputs have the panel height and the same width.
At each aligned coordinate, output 4 appears whenever either panel cell is
nonzero; output 0 appears only when both are zero. Input foreground identities do
not survive, so the rule is a Boolean occupancy union rather than a color merge.

I implemented that direct overlay with shape validation. Competing visible
hypotheses fail within the examples: copying only the top misses bottom-only
cells, copying only the bottom misses top-only cells, XOR misses overlap cells,
and AND misses single-panel cells. No revision was needed after the visible check.
