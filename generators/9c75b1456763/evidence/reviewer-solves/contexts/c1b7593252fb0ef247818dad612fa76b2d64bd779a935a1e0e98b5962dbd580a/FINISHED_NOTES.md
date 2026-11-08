# Solve work log

## Prior exposure

I had already inspected the canonical transformation earlier while repairing this generator, so this is **not** a blind first encounter. During this solve episode I did not reopen the generator, Racket rule, reference solution, private labels, or earlier solution notes. I used only `challenge.json` and the visible input/output pairs.

## Revision 1

### Observation

Each nonzero figure is a 4-connected network of blue (`1`) cells containing exactly one differently colored seed. In every visible output, the seed color appears in all room-center cells across the same connected network, including rooms far from the original seed. Thin connecting paths remain blue.

Comparing changed and unchanged cells gives a local geometric criterion: every recolored cell has nonzero values in all eight surrounding positions. Boundary/path cells have at least one zero in that 8-neighborhood and remain unchanged. Different disconnected networks use their own seed colors.

### Hypothesis

For every nonzero 4-connected component:

1. Find its unique non-blue marker color.
2. Recolor every component cell whose complete 8-neighborhood is nonzero with that marker color.
3. Leave all other cells unchanged.

### Implementation and alternatives

I implemented an iterative 4-neighbor flood fill to isolate components, followed by an 8-neighbor enclosure test against the original input. I rejected two simpler alternatives visible examples contradict:

- coloring only the room that already contains the marker;
- using one global marker for all figures.

Both fail because distant rooms in a connected network change while disconnected networks retain distinct colors.

### Remaining uncertainty

The visible examples consistently contain one marker per component. The implementation intentionally handles a markerless component by leaving it unchanged; no visible evidence requires another behavior.
