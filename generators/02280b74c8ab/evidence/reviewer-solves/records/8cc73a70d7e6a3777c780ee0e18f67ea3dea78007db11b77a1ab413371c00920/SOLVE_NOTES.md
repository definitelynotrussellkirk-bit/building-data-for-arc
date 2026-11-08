# Visible-only solve work log

## Scope and exposure

- Puzzle evidence read: `solve/challenge.json` only, containing four visible input/output examples and two query inputs.
- No generator, rule, canonical solution, private labels, earlier notes, or other agents' work was read during this solve. No reference was consulted during this solve.
- The parent reported earlier canonical exposure during a repair step in the overall workflow. I am the fresh-context solver with no source exposure. The required `--earlier-exposure yes` disclosure conservatively records the parent workflow's exposure, rather than claiming this solve consulted a reference.

## Observations and hypothesis

- Each input contains a larger monochromatic shape in color 6 and another in color 7, plus a compact grid of instruction values. The templates have equal square bounding boxes, of size 2 or 3 in the visible examples and queries.
- A read-only extraction probe identified the largest four-connected component of each template color and printed its crop and the remaining instruction grid. This cleanly separated both templates and the instruction grid in all six inputs.
- Visible outputs support codes 1, 2, 3, 4 as the color-6 template rotated clockwise by 0, 90, 180, 270 degrees; codes 5, 6, 7, 8 use those same rotations for the color-7 template.
- Each instruction cell expands to one template-sized tile. Interior zero cells remain blank tiles. Isolated color-9 cells are excluded from the instruction grid; this matches the third and fourth visible examples.

## Solution revision 1

- Implemented connected-component template extraction, bounding-box extraction of the remaining values 1 through 8, clockwise rotations, and tile expansion.
- No deliberate wrong probe, manufactured failure, or prior solution revision was made.
- Next validation: the prescribed visible-example check and query execution.
