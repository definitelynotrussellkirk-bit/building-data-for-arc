# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — repeated row-count signature

I had not seen this task's generator, Racket rule, private labels, prior solution,
or audit records. I inspected only `challenge.json` and small scripts derived from it.

Each input has three object panels separated by full gray (`5`) columns. Cropping an
object and replacing each row by its count of colored cells revealed that exactly two
panels share the same row-count vector in every demonstration:

- `[3,2,2,3]`, `[1,1,3,1,1]`, `[1,3,4,1,3,4,1]`, and `[1,1,2,2,3]`.

The output is that repeated vector rendered in azure (`8`), with every row packed to
the left and width equal to the largest count. This also discriminates examples where
all objects have the same total area but only two have the same per-row profile.
The two queries have repeated profiles `[1,1,1,4,1,1,1]` and `[4,1,3,4,1]`.
I implemented this rule directly. Remaining uncertainty: the visible data does not
specify a tie-break if no profile repeats; generated queries visibly do repeat one.
