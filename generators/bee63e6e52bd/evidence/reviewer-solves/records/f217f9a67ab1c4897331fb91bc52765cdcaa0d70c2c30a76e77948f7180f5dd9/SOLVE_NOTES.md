# Solve work log

I had no earlier exposure to task `bee63e6e52bd`, its rule, generator, labels, or prior solution notes. I used only the visible examples printed by `review.py blind prepare` and the prepared challenge files.

## Revision 0 — unimplemented baseline

Before coding I treated the existing `NotImplementedError` template as the required failing test baseline. The visible examples appear to contain one connected nonzero orthogonal wall with two aligned endpoints and a zero opening between them. Yellow (`4`) behaves like rays projected through that opening: opening cells continue perpendicular to the gap until a wall or the grid edge, with edge rays shaped by the endpoint geometry. I expect the baseline check to fail only because `solve` is unimplemented.

## Revision 1 — opening-ray projection

I implemented the smallest rule that explains all three visible examples. The nonzero cells form a one-cell-wide orthogonal path with two aligned degree-one endpoints. Cells strictly between those endpoints are the opening. The opening projects straight in both perpendicular directions until a wall or edge. Endpoint rays depend on local geometry: two collinear outward arms produce diagonal edge rays; two perpendicular incident arms produce a chamfer on the exposed side; mixed geometry projects the endpoint-inclusive mouth straight. This is a geometric hypothesis, not a lookup of the hidden rule. The two query shapes are handled by the same endpoint classification.
