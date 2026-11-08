# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Prior exposure declaration

Before this solve episode I had already inspected this task's generator and its
reference-rule binding while repairing it.  Therefore this is **not blind** and
`earlier-exposure` must be recorded as `yes`.  After `prepare`, I kept the
generator, Racket rule, private labels, and earlier solution explanations closed
and used only the displayed examples below.

## Revision 1

The training pairs contain one full-height vertical line of color 8.  Every
nonzero colored cell to its left is copied to the horizontally reflected column
at equal distance on the right.  The source and divider remain unchanged.
Training example 1 shows that multiple source colors are copied independently;
examples 0 and 2 show connected shapes are irrelevant and reflection is
cellwise.  Reflections that would lie beyond the right boundary should be
ignored.  Query 0 also contains pre-existing right-side cells, so the program
starts from a copy of the input and lets a reflected source overwrite only its
own destination, preserving unrelated right-side content.

I implemented this directly: locate the unique full-height 8 column, scan all
columns left of it, and for each color other than 0 or 8 write to
`2 * axis - column` when in bounds.  Remaining uncertainty before checking:
none on the three visible training pairs; overwrite behavior is inferred from
the geometric copy rule rather than demonstrated in a training pair.
