# Occupied-area versus bounding-box-area ordering

`order_metric` is fixed for one episode. `cell_area` is the exact canonical
program; `bbox_area` ranks tight crops by their input-measured bounding-box area
before applying the same one-row-gap vertical packing.

Every scene contains four separated objects with area/bbox pairs 8/8, 5/9,
6/6 and 3/3, so the two rules disagree constructively. Six prefix-stable demo
inputs and four fixed query inputs are available; the last query is a distributed
30x30 stress case. Inputs are identical across settings.

Sequential dependency: A extracts objects and computes the selected metric,
the intermediate is the ordered list of object crops, and B stacks that exact
list. Replacing the bbox-derived order with the cell-area order changes the
protected-Racket result on retained witness cases.
