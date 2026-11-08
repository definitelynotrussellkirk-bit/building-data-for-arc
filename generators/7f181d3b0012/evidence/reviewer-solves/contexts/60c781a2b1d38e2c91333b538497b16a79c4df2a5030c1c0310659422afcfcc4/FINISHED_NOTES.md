# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — vertical reflection appended below

Observed that every output has the same width and exactly twice the input height.
The first half is the input unchanged. The second half is the input rows in reverse
order: example 0 ends with rows 5, 4, ..., 0; example 1's row sequence
`A, A, B, A` becomes `A, A, B, A, A, B, A, A`; and the sparse marks in example 2
appear at vertically reflected row coordinates while retaining their columns.

Hypothesis: concatenate the input with a top-to-bottom reversal of its rows,
equivalently reflect the entire grid across the horizontal boundary immediately
below it. This preserves colors and doubles every color count. A local visible-case
assertion was first run against the untouched stub and failed with
`NotImplementedError`; the minimal implementation then copied the rows and appended
copies in reverse order. No generator, rule, private label, or prior solution was
consulted. Remaining uncertainty is only whether unseen inputs include unusual row
container types; the implementation normalizes rows to lists.
