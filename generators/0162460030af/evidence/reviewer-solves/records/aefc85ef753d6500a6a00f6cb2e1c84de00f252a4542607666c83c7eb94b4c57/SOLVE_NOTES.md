# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Earlier exposure

Before this visible-only solve I had already reviewed this task's generator and
therefore had earlier exposure to the intended rule. During this solve episode I
did not reopen the generator, Racket source, reference solutions, or private
query labels. The program below was checked only against the displayed examples.

## Revision 1 — diagnostic placeholder

I first ran the prepared `NotImplementedError` placeholder as a deliberate
`diagnostic_probe` to verify the solve harness and establish that no visible
example was being accepted accidentally. It errored on all three visible cases,
as expected; this was not presented as a natural solving failure.

## Revision 2 — connected components, horizontal order, right anchor

The visible examples preserve every nonzero object's cells but discard source
colors. Four-connected foreground objects are ordered by their leftmost column.
The rightmost object becomes 8; moving left alternates 2 and 8. This explains:

- example 0: six 2x2 objects become `2,8,2,8,2,8` from left to right;
- example 1: seven differently colored/shaped objects become
  `8,2,8,2,8,2,8` from left to right;
- example 2: two objects become `2,8`.

I implemented an iterative four-neighbor flood fill, sorted components by
minimum column, copied the input, and recolored each entire component according
to its distance from the right edge. Remaining uncertainty is limited to inputs
outside the visible domain (for example, tied leftmost columns); none occur in
the displayed training or query grids.
