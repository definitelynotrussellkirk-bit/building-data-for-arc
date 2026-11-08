# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none known. I did not inspect the task generator, Racket rule,
reference solution, private labels, audit records, or the assigned repair task.

Hypothesis from the three visible demonstrations: split the nonzero cells into
four-connected same-color objects, choose the object with the greatest bounding-box
width, crop to its bounding box, replace that object's cells by color 8, and replace
all other cells inside the crop by 0.

Evidence: the selected widths are 5, 6, and 7 in the three demonstrations. This
explains why the third output is the 9-cell color-2 object rather than the larger
16-cell rectangle: it is one column wider. Competing rules based on pixel count,
area, or rarest color fail at least one visible example.

I first ran the visible-example harness against the untouched stub and observed the
expected `NotImplementedError`. I then implemented the width rule with explicit
4-connected components. Remaining uncertainty: the demonstrations do not specify a
tie-break if two objects have the same maximum width; the implementation uses pixel
count, then height, only to be deterministic.
