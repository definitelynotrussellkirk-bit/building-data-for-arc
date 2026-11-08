# Visible-example solve log

## Revision 1 — chamber seed-count hypothesis

All inputs are gray (`5`) fields containing several disconnected rectangular
regions made only of `0` and red `2`. The output is blank except that one entire
region becomes cyan `8`; its original red cells do not remain red.

For each training pair I counted the red cells inside each 4-connected `0/2`
region. The cyan region is always the unique region with the largest red count:
for example, the first lesson selects the two-red upper-right chamber over the
one-red alternatives, while later lessons include winners with three or five
red cells. Region area and red density do not consistently explain the output.

Implementation: find every 4-connected component whose cells are `0` or `2`,
score it by number of `2` cells, choose the maximum, and paint all of its cells
`8` on a fresh all-zero grid. The visible examples have a strict maximum, so no
tie behavior is needed for the proposed rule.
