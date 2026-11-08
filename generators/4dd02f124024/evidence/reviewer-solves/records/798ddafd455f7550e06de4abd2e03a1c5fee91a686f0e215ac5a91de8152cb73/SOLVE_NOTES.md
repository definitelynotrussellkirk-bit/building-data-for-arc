# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — rare foreign marks identify frames to restore

Earlier exposure: I had not opened this task's generator, Racket rule, reference
solution, private labels, or audit evidence. I used only the visible examples
printed by `python3 review.py blind prepare` and the generated challenge file.

Observation: every scene contains several single-color rectangular frames. A
rare extra color occurs strictly inside some frames. Exactly those marked frames
change: all cells inside their perimeter become background and the perimeter is
left as a clean rectangle. Unmarked frames, including their irregular interior
same-color pixels, remain unchanged.

Implementation hypothesis: choose the least frequent non-background color as
the marker; find complete rectangular perimeter components of every other color;
normalize only boxes containing a marker in their strict interior. This avoids
changing unmarked distractors. Before implementation I ran a visible-example
regression script against the provided skeleton and observed the expected
`NotImplementedError` failure.

Remaining uncertainty: the marker is inferred by rarity, which is strongly
supported by all four demonstrations but could be ambiguous if an object color
were equally rare. The complete-perimeter check narrows the effect to the shown
object type.
