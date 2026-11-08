# Post-repair solve log — ea61d17502dd

Exposure note: this is the required **exposed** solve. I reviewed the task earlier while repairing its generator, but during this episode I used only `solve/challenge.json` and did not consult the generator, Racket source, reference solution, private labels, or earlier explanation files.

## Visible-example reconstruction

Each input contains exactly two crossing nonzero strands:

- the row with the most nonzero cells is the horizontal strand;
- the column with the most nonzero cells is the vertical strand;
- after omitting the crossing, each strand has a majority base color and two cells of a minority marker color;
- the crossing contains one of the two base colors and therefore says which strand is primary.

The output is zero outside a rectangle. Its horizontal bounds are the two horizontal-marker columns. Its vertical bounds include the crossing row and both vertical-marker rows. The rectangle is woven from alternating rows and columns, with parity anchored at its top-left corner.

More specifically, let `near` and `far` be the vertical marker rows closest to and farthest from the crossing row. On even rectangle rows, even columns use the vertical marker color. Inside the vertical-marker band, odd columns use the vertical base, except the near-marker row uses the horizontal base when the horizontal strand is primary. Outside that band, odd columns use the vertical base while even columns use the horizontal marker. On odd rectangle rows, horizontal-primary makes the whole row horizontal base; vertical-primary alternates horizontal base and vertical base by column parity.

## Checks against the three demonstrations

1. The first example has a horizontal-primary crossing. The marker columns are 7 and 8; the vertical markers are rows 2 and 7, while the crossing is row 0. The output rectangle is rows 0..7, columns 7..8 and matches the parity rule.
2. The second example is vertical-primary. Horizontal markers bound columns 0..4 and vertical markers/crossing bound rows 3..8. Odd output rows alternate the two bases, matching vertical priority.
3. The third example is horizontal-primary with a partial horizontal strand. The output rectangle uses marker columns 3..6 and rows 7..14, confirming that strand endpoints themselves do not set the output bounds.

I will implement this directly and make one genuine solve attempt.
