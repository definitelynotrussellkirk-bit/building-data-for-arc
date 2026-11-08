# Post-repair visible-only solve notes

I had earlier rule exposure from reviewing the assigned generator, so this is not a blind solve. During this solve episode I used only `solve/challenge.json` and did not consult the generator, Racket rule, private labels, or prior solution text.

## Hypothesis

The nonzero entries of the first row form an ordered palette, even when separated by zeros. Every nonzero body region is treated as a 4-connected shape. Its exposed cardinal boundary is recolored with the first palette color, then that boundary is removed and the next boundary gets the second color, continuing inward and clamping to the last color if needed. Disconnected one-cell regions are processed independently and therefore get the first palette color.

## Visible evidence

- In training example 1, palette `4,6,7` turns the outer body ring to 4, the next ring to 6, and the center to 7.
- In training example 2, palette `1,6,7,2` produces four nested layers in the large component; detached corner cells become 1.
- The zeros embedded in the header are separators, not a stop marker, because colors after them appear at deeper layers.

## Implementation

I copy the grid, collect all nonzero header colors left-to-right, split nonzero body cells into cardinal components, and repeatedly peel each component's cardinal boundary. This is my first attempted implementation for the episode.
