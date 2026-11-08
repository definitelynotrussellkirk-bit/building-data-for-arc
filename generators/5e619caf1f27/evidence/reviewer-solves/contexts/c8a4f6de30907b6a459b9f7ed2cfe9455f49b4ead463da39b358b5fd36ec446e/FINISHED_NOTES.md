# Visible-only solve work log

This is a concise authored work log, not a captured token-level model trace.
Earlier rule exposure: no. No generator, reference, canonical labels, previous
solution explanations, or audit evidence was consulted.

## Observation and selected hypothesis

The four visible pairs preserve a two-color rectangular object and add a
rectangular surrounding band in the interior color. The band is two cells
wide in examples 0, 2 and 3. In example 1 the object is one row from the top
edge and the added band is uniformly one cell wide on all four sides.
The selected algorithm uses thickness min(2, all four available margins).
Input/output shapes are respectively 16x17, 14x16, 15x14, and 17x17 in both
members of the four pairs. Query inputs are 18x16 and 16x17; outputs unknown.

A constant two-cell band clipped separately at grid edges was considered
and rejected during inspection because it disagrees with visible example 1.
That was an analytical comparison, not a submitted failed solve revision.
The first submitted revision implements the uniform-margin hypothesis.

## Limits

Four examples do not identify every possible radius rule. The submitted
solver assumes the visible domain: a single two-color filled rectangle on
zero background, an interior color, and a surrounding uniform band.
No masked-query correctness claim is made.

## Check result

Revision 1 completed and matched all 4 of 4 visible examples. The checker
withheld masked-query correctness; no further revision was justified.
