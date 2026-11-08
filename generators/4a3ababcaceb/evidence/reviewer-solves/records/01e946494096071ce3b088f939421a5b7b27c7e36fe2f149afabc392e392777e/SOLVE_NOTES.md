# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Before this solve I had not opened any generator, canonical rule, reference
solution, private label, audit record, or task-specific prior explanation.  I
used only the visible grids emitted by `review.py blind prepare`.

The full rows and columns of 9 divide every example into 3x3 rooms.  Exactly one
room contains color 3 and only that room changes.  Its replacement is color 8
at exactly the positions occupied by color 2 in one other room; all remaining
positions in the target room become 0.

There can be multiple rooms containing color 2.  In train 0 the copied room has
seven 2s plus exactly one foreign colored cell, while the other candidate has
three foreign cells.  In train 1 the copied room has six 2s plus exactly one
foreign cell, while the other candidate is an undecorated 2-shape.  Train 2 has
only one 2-room.  This supports the working selection rule: prefer a 2-room with
exactly one nonzero non-2 marker; when there is no such room, use the nearest
2-room.  Manhattan distance and blue support size are deterministic tie-breaks.

The two visible queries reinforce the distinction: query 0 offers candidates
with three versus one foreign cells, and query 1 offers an undecorated blue
cross versus a blue pattern with one foreign cell.  Remaining uncertainty: the
examples do not prove the tie-break order if several one-marker rooms occur.
