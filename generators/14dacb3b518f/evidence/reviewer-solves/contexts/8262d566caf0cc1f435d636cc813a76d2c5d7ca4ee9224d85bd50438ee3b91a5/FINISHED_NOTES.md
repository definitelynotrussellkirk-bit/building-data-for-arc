# Post-repair solve notes

This is a human work log based only on `solve/challenge.json`. I had already seen the task rule while repairing the assigned generator, so this is an exposed solve and will be declared with `--earlier-exposure yes`.

## Revision 1 hypothesis

All foreground objects begin as color 6. The output recolors each 4-connected object uniformly:

- objects enclosing at least one background pocket become 8;
- objects with no enclosed pocket become 2;
- background remains 0.

Evidence in the visible examples:

- Train 1 has a repeated hourglass-like holed component recolored 8, while an open/L-shaped component and a large filled rectangle become 2.
- Train 2 shows a rectangular frame becoming 8, an open irregular outline becoming 2, and a dense component with a single enclosed zero becoming 8.
- Train 3 rules out a size-only rule: the large filled rectangle becomes 2 while the smaller cavity-bearing component becomes 8.
- Train 4 includes both a thin line/plus-like solid becoming 2 and a non-thin component with two enclosed pockets becoming 8.

Implementation: find 4-connected same-color components, inspect zero regions inside each component's bounding box, and recolor 8 iff any such region does not touch the bounding-box boundary. This also handles nonrectangular and multi-hole components rather than checking only for rectangular frames.
