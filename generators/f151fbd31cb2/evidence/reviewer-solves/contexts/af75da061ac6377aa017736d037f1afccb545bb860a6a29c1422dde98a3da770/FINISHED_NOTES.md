# Solve notes

## Revision 1 — dual-key family selection

The three visible pairs contain disconnected green objects from two recognizable families: L triominoes and plus pentominoes. There are also two singleton non-green cells.

Observed mapping:

- singleton `1` selects L triominoes;
- singleton `4` selects plus pentominoes;
- singleton `2`, `6`, or `8` is the replacement color;
- only green components of the selected shape family change; keys and the unselected family remain unchanged.

Evidence from the visible pairs:

1. With shape key `1` and color key `2`, both L components become `2`, while the plus stays green.
2. With shape key `4` and color key `2`, the plus becomes `2`, while both L components stay green.
3. A second key-`4` example repeats the plus-only recoloring across a larger grid and multiple pluses.

Implementation plan: find the singleton keys, collect 4-connected color-3 components, normalize each component to identify L versus plus, and recolor the selected family on a copy of the grid. I am not using object count or total area because those vary across examples and are not what the singleton shape key encodes.
