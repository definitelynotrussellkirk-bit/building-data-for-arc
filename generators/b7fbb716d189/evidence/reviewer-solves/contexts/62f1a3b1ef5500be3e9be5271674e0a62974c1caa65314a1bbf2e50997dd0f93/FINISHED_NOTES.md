# Solve work log

## Exposure boundary

Before this visible-only episode I had already inspected the selected rule while repairing its generator, so earlier rule exposure is **yes**. During this episode I did not reopen the generator, Racket rule, canonical/reference solutions, private labels, or prior solution explanations. This is a human work log based on the displayed lesson only.

## Revision 1 — crop the motif, then obey the corner token

The only colors 1–4 appear as a single isolated corner cell; the remaining nonzero colors form one compact motif. In each demonstration the output is the motif's tight bounding-box crop with internal zeroes preserved.

- Token `4`: train examples 0 and 2 both equal the matrix transpose of that crop, despite token 4 occupying different corners. This rules out corner position as the operation selector.
- Token `2`: train example 1 equals a 90-degree clockwise rotation of the crop.
- Both queries visibly contain token `2`, so the demonstrated clockwise operation completely determines both query answers. Tokens 1 and 3 are not demonstrated and are deliberately left unsupported rather than guessed.

Implemented the tight crop plus the two demonstrated operations. Remaining uncertainty is limited to unseen token meanings 1 and 3, which do not occur in either query.
