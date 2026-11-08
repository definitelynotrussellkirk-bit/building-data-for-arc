# Solve work log

## Prior exposure

Before this visible-only solve I had already inspected this task's generator and authority during the assigned review, so earlier rule exposure is **yes**. During this solve I did not reopen the generator, Racket source, private query labels, reference solutions, or previous solution explanations. I used only the prepared visible examples, `solve/challenge.json`, my own Python, and the check command.

## Revision 1

Hypothesis from the five visible pairs:

1. Every nonzero input dot is the centre of a clipped 3×3 output block.
2. The centre keeps the input dot's colour. The eight surrounding cells use the colour of the other dot in the same row, not necessarily the dot's own colour.
3. Every same-row and same-column dot pair is joined by colour 5 at every second cell, working inward from both endpoints. These guides are painted after the 3×3 blocks.
4. Multiple disconnected rectangles are all transformed; border blocks are clipped to the unchanged canvas.

I implemented that rule directly. As a local visible-only probe, I applied the program to all five training inputs from `challenge.json`; each output matched exactly. The two test inputs each contain two rectangles, including same-row-colour rectangles that distinguish row-partner colour from a simple opposite-global-colour guess.

Remaining uncertainty before the official visible check: none about the observed domain; inputs outside aligned rectangle scenes were not inferred and are not needed here.
