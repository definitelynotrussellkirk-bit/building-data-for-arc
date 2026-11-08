# Solve work log

I had not opened this task's rule, generator, notes, reference solution, private
labels, or audit evidence. I used only the visible examples produced by blind
preparation and my own Python probes.

## Hypotheses and probes

1. The colors `3` and `2` are endpoints in a four-neighbor maze; `5` cells are
   walls and `0` cells are traversable. A first hypothesis was “paint one
   shortest path.” That explains training example 1 but not examples 0 and 2:
   their outputs omit cells that can vary between equally short routes.
2. I tested whether the blue `8` cells were ordinary graph articulation points
   separating the endpoints. This fails on example 2, where the highlighted
   prefix is avoidable by a longer route.
3. The consistent rule is narrower: paint an intermediate cell exactly when it
   belongs to **every shortest path** from `3` to `2`. For each visible example I
   computed distances from both endpoints, restricted to the shortest-path DAG,
   counted shortest paths through each cell, and compared the forced cells with
   the provided output. The exact highlighted counts matched: 13, 6, and 5.

## Implementation

`solution.py` runs two breadth-first searches, counts paths forward and backward
through the shortest-path DAG, and changes a non-endpoint cell to `8` when
`paths_from_start[cell] * paths_to_target[cell]` equals the total number of
shortest paths. It preserves the input object by returning a copied grid.

## Verification record

Before implementation I created a visible-example test and ran:

```sh
cd /mnt/data/arcpuzzles_review_090355
python3 -m pytest -q /tmp/test_blind_d4f2f542248a.py
```

It failed at the original `NotImplementedError`, as expected. The same test is
rerun after implementation, followed by the packet's blind check. Remaining
uncertainty is limited to unseen malformed inputs (missing endpoints or no route);
the implementation conservatively returns an unchanged copy in those cases.
