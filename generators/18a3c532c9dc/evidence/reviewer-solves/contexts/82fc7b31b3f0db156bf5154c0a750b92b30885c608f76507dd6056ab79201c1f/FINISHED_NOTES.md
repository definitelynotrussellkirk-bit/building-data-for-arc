# Post-repair solve work log

This is a human visible-example work log. I had earlier rule exposure during the
generator review, so this episode is not blind. During this solve phase I did not
open the generator, Racket rule, canonical/reference solutions, private labels, or
my earlier blind-solve explanation; I used only the prepared visible examples.

## Revision 1 hypothesis

Every 8×8 input divides naturally into four 4×4 quadrants and every output is 4×4.
At each output coordinate, the four corresponding input cells are combined while
zero acts as transparent background.

Visible precedence probes from train example 0:

- Output (1,0) is 1 when TL=8, TR=1, BL=4, BR=9, so TR outranks all others.
- Output (0,0) is 4 when TL=0, TR=0, BL=4, BR=9, so BL outranks BR.
- Output (2,1) is 4 when TL=8, TR=0, BL=4, BR=0, so BL outranks TL.
- Output (3,0) is 9 when TL=8, TR=0, BL=0, BR=9, so BR outranks TL.

These observations imply priority `TR > BL > BR > TL`: start from TL, then replace
with nonzero BR, then nonzero BL, then nonzero TR. I implemented that coordinatewise
and return a half-height by half-width grid. I expect one solve revision to match
all visible examples; no deliberate negative or diagnostic-only revision was made.
