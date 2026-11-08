# Blind solve notes — ae7376fe4957

Source policy: visible examples only. I did not inspect a generator, canonical rule,
reference solution, private label, audit record, or prior explanation.

## Observations and revisions

1. The output is a tight crop of a selected subset of the sparse nonzero cells;
   blue `1` is a marker and is erased. Some distractors can lie inside the crop
   (train 1), so a plain bounding box or nearest-component rule is insufficient.
2. I first considered proximity, connected components, Voronoi regions, color
   frequency, and convex hulls. Train 1's interior `2` defeats these simple rules.
3. In every visible input, the `1` marker lies on a unique straight line with at
   least two other colored cells. This appears to be the construction key.
4. Train 0 has three cells after the marker on a unit diagonal. For the first two
   guide colors, their duplicate occurrence has the same displacement `(1, 0)`;
   the third guide color's mate has a different displacement. Keeping the
   dominant repeated displacement exactly yields the output. Test query 1 is an
   exact translated/color-renamed copy of this construction.
5. Train 1's primitive guide direction is `(1, -2)`. Column parity is invariant
   along that direction; every retained cell has the marker's odd-column parity,
   while both distractors are in even columns. Test query 0 has guide direction
   `(2, -1)`, for which row parity is invariant, so I use the analogous row class.
6. Train 2 has guide parameters `-1,+1`, symmetric about the marker. Its intended
   cells form the marker's spatial point-cloud cluster; the three left-side
   distractors are separated by the unique largest bridge of the Euclidean MST.
   I use this only for the symmetric-guide case, since it is invalid for train 1.

## Expected query behavior

- Query 0: retain non-marker cells on odd rows (same row parity as the marker),
  then tight-crop. The lone even-row `3` at `(12,0)` is discarded.
- Query 1: retain both `6` cells and both `4` cells, discard the `3` pair and the
  remote `2`, yielding `[[6,0],[6,4],[0,4]]`.

This is a finite-example hypothesis with explicit branches; the visible examples
are too small to establish a single universal characterization. I stop after a
solver that exactly matches all visible pairs and gives deterministic query outputs.
