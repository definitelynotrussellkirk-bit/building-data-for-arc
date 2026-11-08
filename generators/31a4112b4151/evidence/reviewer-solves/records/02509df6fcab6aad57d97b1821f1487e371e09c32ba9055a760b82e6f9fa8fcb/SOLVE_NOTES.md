# Solve work log

I had not seen the task's generator, Racket rule, private labels, reference
solution, or prior solution notes before this solve. I used only the prepared
visible examples and `challenge.json`.

## Revision 1 — relative-offset stamping

The nonzero non-9 cells form a motif. One 9 is embedded beside that motif and
acts as its template anchor. The other 9 cells are destination anchors. For
example, in train 1 the three colored cells are at offsets `(1,-1)`, `(1,0)`,
`(1,1)` from the nearby 9; applying those offsets to every 9 exactly produces
the output, including clipping the rightmost copy at the grid boundary. Train
2 gives the same evidence with a vertical line, and train 3 confirms clipping
when most of a copy lies outside the grid.

I wrote a visible-example regression harness first. It failed on the supplied
`NotImplementedError`, establishing the red test. The implementation then:

1. treats the most frequent color as background and 9 as the marker color;
2. collects all other cells as the motif, preserving their colors;
3. selects the marker minimizing the motif's maximum Chebyshev distance, with
   total Manhattan distance and local adjacency as deterministic tie-breakers;
4. stamps every motif offset at every 9 and clips out-of-bounds cells;
5. clears all original content by constructing the result from background.

The closest-marker criterion is needed because a destination marker can happen
to touch part of the exemplar (train 1), while the true template marker is the
one around which the complete motif is most compact. Remaining uncertainty is
limited to unseen cases with an exact geometric tie between two candidate
markers; the visible generation pattern provides a unique compact anchor.
