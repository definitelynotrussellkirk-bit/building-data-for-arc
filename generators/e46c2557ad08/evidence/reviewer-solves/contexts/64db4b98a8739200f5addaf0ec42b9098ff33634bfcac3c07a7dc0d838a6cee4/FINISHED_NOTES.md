# Blind visible-only solve: e46c2557ad08

I inspected only the public preparation output and its visible grids. I have not opened any generator, canonical rule, private answer, task notes, reference solution, or audit record for any task before this attempt. The earlier environment work concerned extraction, workflow code and offline runtime setup only.

## Observations
- Example 0 is 8 rows by 10 columns on both sides. Three isolated horizontal pairs of 5 become 8. A horizontal triple and a vertical pair remain 5.
- Example 1 is 9 by 11 on both sides. The isolated horizontal pair changes; the 2 by 2 block and vertical pair do not.
- Example 2 is 13 by 11 on both sides. Both horizontal pairs change, while the vertical pair and horizontal run of four do not.
- Query inputs are 8 by 11 and 11 by 10. Their output shapes and correctness have not been revealed.

## Hypothesis and visible alternatives
The transformation recolors exactly four-connected gray components consisting of two horizontally adjacent cells, from 5 to 8. All other cells remain unchanged. Recoloring any size-two component would wrongly change vertical pairs. Recoloring any adjacent horizontal pair would wrongly change the square and longer runs. Recoloring all horizontal lines would wrongly change length-three and length-four components.

## Revision 1
Use a four-neighbor component traversal, then select size two with equal row coordinates. This tests the rule inferred above without consulting hidden labels. No failed solution was manufactured; this is my first attempted implementation.

## Limits
Visible examples do not disambiguate all imaginable color, diagonal-contact, or nonrectangular-input variations. The public challenge uses colors 0 and 5 with changes to 8. I keep those demonstrated roles and make no claim of universal induction. Query correctness is reserved for independent maintainer scoring.
