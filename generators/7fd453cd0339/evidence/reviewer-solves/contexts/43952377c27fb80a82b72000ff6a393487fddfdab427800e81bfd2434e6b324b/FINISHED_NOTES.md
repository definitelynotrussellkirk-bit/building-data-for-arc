# Visible-only solve notes

The three demonstrations consistently replace every nonzero orthogonally connected filled rectangle by the distinct corners of that component's bounding box. Background remains zero and grid dimensions do not change.

I treated disconnected regions independently even when they share a color. This matters for query 0, where color 5 appears in a top 2×3 rectangle and a separate bottom 1×4 line. A one-row or one-column component has only two distinct bounding-box corners, so set deduplication is required.

Implementation: flood-fill each same-color component, compute its minimum/maximum row and column, and write its distinct bounding-box corners into a fresh zero grid. I did not consult the Racket source, generator source, private labels, reference solution, or previous solve notes during this solve. I had already seen the intended rule while repairing the generator, so earlier exposure is yes.
