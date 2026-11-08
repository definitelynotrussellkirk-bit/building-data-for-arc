# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none. I had not opened this task's generator, authority rule,
reference solution, private labels, or prior solve notes.

Observation: the isolated nonzero payload in each training input becomes the
entire output, while the single top-left cell acts as an instruction rather than
payload. For marker 1, the cropped payload is rotated 90 degrees clockwise; for
marker 2 it is rotated 180 degrees; for marker 3 it is rotated 270 degrees
clockwise. This exactly explains all three visible pairs, including the third
pair's 3x5 to 5x3 shape change.

Hypothesis: remove the top-left marker, crop to the bounding box of the remaining
nonzero cells (retaining zeros inside the box), then rotate clockwise by marker
modulo 4. Marker 4 therefore means a full turn / identity.

Implementation: enumerate payload cells excluding (0,0), crop their bounding
rectangle, and apply list-matrix clockwise rotation once per turn. Remaining
uncertainty is only whether unseen inputs can contain no payload; the function
returns an empty grid for that degenerate case.
