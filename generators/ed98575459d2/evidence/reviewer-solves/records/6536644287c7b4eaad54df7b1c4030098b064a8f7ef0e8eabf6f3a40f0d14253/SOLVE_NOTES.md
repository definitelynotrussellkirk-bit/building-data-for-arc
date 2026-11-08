# Post-repair solve notes

## Visible-pattern hypothesis

The cyan 8-cells are fixed walls.  They divide each grid into one or more
4-connected non-8 chambers.  Inside each chamber, each column is treated
independently: retain the nonzero values in their original top-to-bottom order,
clear the chamber cells in that column, and place those values into the highest
available chamber rows.  This explains:

- the no-divider example, where every colored cell rises to row 1 within its column;
- vertical-divider examples, where each side is processed independently;
- the horizontal-divider example, where lower-chamber cells stop immediately below
  the horizontal wall instead of crossing it;
- stacked values (for example the two 2s) retaining their order and count.

No recoloring or horizontal motion is visible.  I will implement the rule by
finding 4-connected components after excluding color 8, then compacting each
component column upward.
