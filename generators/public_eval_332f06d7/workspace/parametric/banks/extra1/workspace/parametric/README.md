# `public_eval_332f06d7` authoring family

The canonical program treats the color-0 rectangle as a boat. It enumerates
all top-left placements where the boat's complete footprint avoids the wall,
retains the placement-graph component containing the initial boat, and moves
the boat to the reachable dead end nearest the equal-size color-2 destination.
The old boat cells become corridor color 1.

`finish=trace_route` additionally recolors to 9 the corridor cells swept by
the selected start-to-end route, excluding the final boat. The retained
counterfactual marks every reachable placement, including unused branches.

```bash
python3 review.py run pytest -q generators/public_eval_332f06d7/tests
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight \
  public_eval_332f06d7 --root . --out ../checks/public_eval_332f06d7/preflight
```
