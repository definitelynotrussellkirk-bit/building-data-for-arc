# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none. Before this solve I had read only the packet-level
instructions and assignment text; I had not opened the blind task's generator,
rule, prior notes, solutions, private labels, or the assigned repair generator.

The three examples all preserve columns and copy whole input rows. Numbering the
five input rows 0 through 4, every output uses the same 17-row order:
`0,1,2,3,4,3,2,1,0,1,2,3,4,3,2,1,0`. I interpret this as two complete vertical
mirror/bounce periods, avoiding a duplicated endpoint at each turn. I implemented
that row-index walk directly and generalized it to arbitrary nonempty heights.
The only alternative I considered was a fixed five-row special case, rejected
because the reflection rule itself is clearer and equally small. Remaining
uncertainty is only whether hidden inputs could use a different height; the code
handles that naturally under the same rule.
