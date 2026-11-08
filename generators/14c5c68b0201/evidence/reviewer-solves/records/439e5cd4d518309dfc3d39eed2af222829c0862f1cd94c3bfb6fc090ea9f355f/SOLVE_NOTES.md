# Solve work log

## Prior exposure

I had not opened the blind task's generator, canonical rule, reference solution,
private labels, audit records, or prior solve explanations. I used only the public
examples produced by `solve_episode.py blind prepare` and local Python checks.

## Revision 1 — periodic extension of each seed

The grids contain one or more rectangular zero canvases inside a dominant frame
color. Each canvas contains a compact colored seed. Comparing the demonstrations
showed that the output repeats that seed in both dimensions:

- the vertical period is the colored seed's bounding-box height;
- the horizontal period is the colored seed's bounding-box width;
- colored cells retain their residues modulo those periods, including cells that
  wrap across a tile boundary;
- all other cells in the canvas remain zero, and the frame remains unchanged.

This explains the apparent extra cell in training example 1: the rightmost seed
cell repeats one period to the left. It also handles training example 2's two
independent canvases with different seed sizes.

I implemented a general solver that identifies the dominant border/frame color,
finds each 4-connected non-frame canvas, derives the seed bounding box and residue
map, and fills only that canvas. Before implementation, a visible-example unit
test failed on the untouched `NotImplementedError`; after implementation I used
that same test and the official visible-only checker. Remaining uncertainty is
limited to unseen layouts that violate the demonstrated framed rectangular-canvas
structure or contain conflicting colors at the same periodic residue.
