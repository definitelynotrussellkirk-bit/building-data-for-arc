# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — connected rooms with exactly one marker

Earlier exposure: none. I had not opened task `71492f8cef8f`'s generator, Racket
rule, reference solutions, private labels, audit records, or earlier solve notes.

Hypothesis from the three visible examples: color 5 is an impermeable wall. Treat
all non-5 cells as four-connected components. A component containing exactly one
cell whose color is neither 0 nor 5 is a room with a single marker; replace every
0 in that component with the marker's color. Components with zero markers or two
or more markers remain unchanged. This also explains train example 1, where a
single color-4 marker replaces a boundary wall cell but is still four-connected
to the room it fills.

Probe: a local pytest compared `solve` with all three visible training outputs.
The initial skeleton failed with `NotImplementedError`, as expected. I then
implemented the component rule directly. Alternatives considered were filling
rectangular wall-bounded boxes or filling every room containing a repeated color;
the irregular lower partition in train example 2 and the two-marker unchanged
rooms reject those alternatives. Remaining uncertainty is limited to unseen
arrangements not represented by the visible examples, such as ragged grids or
non-5 wall colors.
