# Solve work log

Earlier exposure before this episode: none known for task `ea8116b3e778`; I did not inspect its generator, rule, notes, solutions, audit records, or private labels.

## Revision 1 — four-way reflection around the green marker

The color-3 object is always a 2×2 marker.  In the second training pair, a color-2 shape present southeast of that marker is copied into the other three quadrants.  In the third pair, the same completion happens from a northeast source.  The first pair is already closed under both reflections and therefore remains unchanged.

I modeled the marker's horizontal and vertical center lines using the sums of its minimum and maximum row/column indices.  Every color-2 cell is copied to its original location, its horizontal reflection, its vertical reflection, and the composition of both.  Reflections outside the grid are ignored, though all visible examples appear designed so the complete orbit fits.

Alternatives considered: rotating one connected component four times, or copying only the component nearest the marker.  Cellwise horizontal/vertical reflection is simpler and exactly explains all three visible examples, including disconnected portions of the motif.
