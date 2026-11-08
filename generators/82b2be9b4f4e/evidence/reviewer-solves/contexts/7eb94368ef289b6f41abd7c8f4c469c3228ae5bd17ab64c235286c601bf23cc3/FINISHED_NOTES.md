# Solve notes

Human work log using only `solve/challenge.json` during this solve phase.

The isolated bottom-left nonzero cell acts as a color key. I clear that marker,
find 4-connected objects of the same color, select the largest one, crop its
bounding rectangle including internal background cells, and double every row
and column. The three visible outputs all match this: the first and third are
6x6 or 6x4 doubled crops, while unrelated colors and smaller same-color objects
are discarded. One implementation should cover both test inputs; no reference
source was consulted during this phase. Earlier rule exposure is declared yes
because this is the reviewed generator task.
