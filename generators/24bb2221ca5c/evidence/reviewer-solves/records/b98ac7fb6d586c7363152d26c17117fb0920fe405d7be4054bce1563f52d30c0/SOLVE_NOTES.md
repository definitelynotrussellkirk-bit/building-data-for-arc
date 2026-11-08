# Solve work log

## Exposure declaration

I had substantial earlier exposure to this task family while reviewing the generator before this fresh solve. After `prepare`, I used only the public `solve/challenge.json` to write and assess this revision; I did not inspect the Racket authority, private labels, the frozen generator snapshot, or an earlier solution.

## Revision 1 hypothesis

The three visible examples point to object-local topological enclosure rather than visual rectangle completion:

- closed monochrome boundaries have their enclosed zero cells recolored to the boundary color;
- an almost-closed object with a side opening stays unchanged because its interior is 4-connected to the local exterior;
- a boundary with a missing corner still fills, showing that diagonal contact is not an escape route;
- a connected nonrectangular object can enclose several zero regions, and every enclosed region fills;
- disconnected objects, including objects of the same color, must be processed as separate 4-connected components.

I therefore implemented the following directly from the public demonstrations:

1. enumerate each nonzero color's 4-connected components;
2. take each component's bounding box;
3. flood only zero cells from that box's boundary using 4-neighbor motion;
4. recolor the zero cells not reached by that flood with the component color;
5. leave nonzero cells and exterior-reachable zeros unchanged.

This avoids treating a corner gap as open under 8-connectivity, avoids merging disconnected same-color shapes, fills multiple and nonrectangular cavities, and does not fill a side-open decoy.

## Alternatives considered

- Filling every component bounding box fails the visible side-open negative and would overwrite exterior pockets around irregular objects.
- Filling only rectangular interiors fails the visibly irregular multi-cavity example.
- Treating all cells of one color as a single object can bridge disconnected objects.
- Using 8-neighbor background reachability would make the corner-gap enclosure incorrectly open.

## Remaining uncertainty

The public examples do not settle ownership when another colored object lies inside a cavity or when different components overlap one another's bounding boxes. The implementation conservatively fills only zeros and never overwrites existing colors. Masked-query feedback is intentionally unavailable, so stopping is based only on exact agreement with all visible demonstrations.
