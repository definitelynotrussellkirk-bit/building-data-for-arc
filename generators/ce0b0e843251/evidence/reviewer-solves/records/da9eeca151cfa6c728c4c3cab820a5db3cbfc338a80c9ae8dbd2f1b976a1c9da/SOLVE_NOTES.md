# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.
# Blind solve: ce0b0e843251

## Exposure and evidence boundary

No generator, Racket rule, canonical task entry, prior solution, notes, audit,
or private query label was read before this solve. I used only the public
preparation output and challenge.json. No earlier exposure to this task is known.

## Initial observations and hypothesis

The three examples preserve their shapes: 10 rows × 12 columns, 9 rows × 12
columns, and 12 rows × 10 columns. Color 7 forms the outer border and color 5
partitions the interior. Every nonempty chamber has a single colored marker;
the output fills that entire chamber with the marker color. Empty chambers stay
zero. The third example changes the partition orientation, supporting connected
regions rather than a fixed row or column operation.

The two queries have inputs of 10 rows × 12 columns and 9 rows × 12 columns;
their output dimensions and labels are unknown.

## Revision 1 — solve attempt

Implement four-connected component search through cells other than 5 and 7.
Fill each component from its unique nonzero marker; preserve unmarked components.
Use the wall colors observed consistently in all three visible examples. A
geometric rectangle-fill implementation is an alternative, but connected
components express the observed barrier behavior more directly. Mixed-marker
components are undefined by these examples and raise an explicit error.

No failed attempts were manufactured. The checker will evaluate the visible
examples and query execution only; masked-query correctness remains unknown.
