# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — equality table

Earlier exposure: I had already inspected the generator and reference-facing review
evidence during the repair, so this is honestly marked exposed. During this solve I
used only the visible challenge above.

Each input has column labels along the top border and row labels along the left
border, with a blank interior. The output removes both borders. At output `(r-1,
c-1)`, it writes the left-border label exactly when it equals the top-border
label; otherwise it writes 0. This explains every visible nonzero, including all
third-and-later repeats in the two 8x9 examples. I implemented that rule directly.
