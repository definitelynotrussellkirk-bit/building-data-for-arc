# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — visible-only hypothesis before implementation

I had not seen this task's generator, reference rule, private query labels, prior
solutions, or audit material. The four demonstrations all retain the input and
add cells at the same column in the row reflected across the horizontal center:
`(r, c) -> (height - 1 - r, c)`.

The decisive conflict case is training example 1. Row 0 would mirror a color 6
onto row 9 column 0, but that destination already contains color 4 and the output
keeps 4. Therefore this is not wholesale row replacement. It is completion of
missing mirror partners: copy a nonzero source only when the mirrored destination
is background 0. Existing colored cells on either side are givens and remain
unchanged. Training examples 2 and 3 support bidirectional completion and odd
heights; the middle row maps to itself.

I first ran the check against the supplied `NotImplementedError` placeholder to
record a genuine red attempt. It produced an execution error with 0/4 visible
examples passed, as expected before implementation.

Alternatives rejected:

- Reflect only the denser occupied half: examples 2 and 3 require additions in
  both directions.
- Replace each row by its reflected partner: example 1 would destroy the given 4.
- Mirror left/right or rotate 180 degrees: added cells stay in the same columns.

The implementation reads from an immutable copy of the input and writes only to
background destinations in a separate result, so iteration order cannot create
extra propagation or overwrite a given conflict.
