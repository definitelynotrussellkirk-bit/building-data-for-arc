# Solve work log

## Prior exposure

I had not opened task `694d3ee0b12a`'s generator, canonical rule, reference
solutions, private labels, audit evidence, or prior solve explanations before
this attempt. I only read the packet-level directions and the generated visible
challenge.

## Revision 1 — Cartesian row/column intersections inside each frame

Each colour-7 rectangle is an independent panel. Across the three visible
training examples:

- colour 2 selects one or more **interior rows**;
- colour 3 selects one or more **interior columns**;
- the one other non-background/non-frame colour in that panel is the paint
  colour; and
- the output paints the Cartesian product of those selected rows and columns,
  overwriting a 2 or 3 when an intersection already contains one.

Examples checked manually:

- train 0, lower panel: two 2-rows × one 3-column produces two colour-6 cells,
  including replacement of the original 3 at one intersection;
- train 1, lower panel: three 2-rows × two 3-columns produces six colour-8
  intersections;
- train 2, upper panel: two 2-rows × two 3-columns produces four colour-5
  intersections.

The existing isolated paint-colour cell is retained; it identifies the colour
rather than serving as an endpoint. I considered connecting individual 2/3
pairs or extending lines from the paint marker, but the full 3×2 example rules
those out.

Implementation finds separate 4-connected colour-7 rectangular borders, reads
all cues from the original grid, and applies the product independently per
panel. Remaining uncertainty is limited to unseen malformed/touching frames or
panels with more than one extra colour; the visible task consistently has one
complete frame and one paint colour per panel.
