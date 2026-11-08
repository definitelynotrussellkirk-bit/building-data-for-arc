# Solve work log

## Exposure declaration before solving

I had not opened task `ebdf2e943f3f`'s generator, Racket rule, canonical record,
reference solutions, private labels, prior solve explanations, or audit records.
Before this solve I only read the packet-level instructions and the visible examples
printed by `python3 solve_episode.py blind prepare`.

## Visible pattern and hypothesis

Every colored object in the four demonstrations is an incomplete solid rectangle.
For each nonzero 4-connected same-color component, the output keeps the grid size
and fills every background cell in that component's axis-aligned bounding box.
Separate components are handled independently, including two components of the
same color in train example 2.

Specific checks from the visible data:

- Train 0 has two three-cell L shapes; each becomes a 2 × 2 block.
- Train 1's color-7 component spans 2 rows × 4 columns and becomes all 8 cells;
  the color-8 and color-4 L shapes each become 2 × 2 blocks.
- Train 2 shows that disconnected same-color components must not be merged into
  one large bounding box.
- Train 3 confirms both orientations of a missing corner.

The two queries therefore require adding the missing corners of the 2 × 2 objects;
in query 1 the six-cell color-8 component should fill its 4 × 2 bounding box.

## Program design and probes

I used a row-major scan and breadth-first search over four-neighbor cells of the
same nonzero color. For each component, the program computes minimum/maximum row
and column and fills background cells in that rectangle. Existing nonzero cells
are preserved so one object's completion cannot overwrite another colored cell.

Before implementation, an inline test against the untouched template failed with
`NotImplementedError`, as expected. After implementation I tested the solver
against all four visible train pairs from `challenge.json` and added small probes
for disconnected same-color components, an already complete rectangle, and an
empty grid. No alternate rule was needed after those probes.

## Alternatives and remaining uncertainty

A color-global bounding box is contradicted by train example 2, which has two
far-apart color-7 components. Eight-neighbor grouping is unnecessary and could
incorrectly merge diagonally touching objects; the visible objects are connected
orthogonally. Filling only a single missing corner is less general than the
rectangle-completion rule demonstrated by the 2 × 4 object. The main remaining
uncertainty is whether unseen lawful inputs ever contain overlapping component
bounding boxes; preserving pre-existing nonzero cells is the conservative choice.
