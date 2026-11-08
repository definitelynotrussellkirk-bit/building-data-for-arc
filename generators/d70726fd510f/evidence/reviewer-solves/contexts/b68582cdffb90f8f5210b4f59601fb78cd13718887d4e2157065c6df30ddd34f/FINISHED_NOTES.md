# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — panel XOR

Earlier exposure: none. Before this solve I had only read the packet-level workflow and
assignment; I did not open this task's generator, rule, private labels, prior solutions,
or any generator assigned for repair.

Hypothesis: the full-height color-4 column is a divider between two equal-width binary
patterns. The output marks, in color 2, exactly the positions occupied on one side but
not both (symmetric difference / XOR). This matches train 0 row by row, including the
zeros where both panels are occupied, and spot checks on trains 1 and 2. The program
finds the centered solid non-zero divider, treats any non-zero panel cell as occupied,
and emits 2 for XOR and 0 otherwise.

Remaining uncertainty: the visible data always has one centered divider and background
0, so the implementation intentionally rejects layouts outside that demonstrated form.
