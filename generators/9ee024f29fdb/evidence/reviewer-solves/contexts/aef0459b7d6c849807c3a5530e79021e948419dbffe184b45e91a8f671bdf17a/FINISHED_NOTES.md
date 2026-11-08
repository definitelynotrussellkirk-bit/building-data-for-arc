# Solve work log

## Exposure declaration

I had already inspected the repaired task during generator review, so this is an
**exposed post-repair solve**, not a blind solve. During this solve I used only
`solve/challenge.json`; I did not reopen the generator, Racket rule, reference
solutions, prior solution explanations, or private query labels.

## Revision 1

The three visible examples share zero-valued separator rows and columns at
zero-based indexes divisible by four. Those lattice locations become 0 even
when the input contains a nonzero distractor. At every other location, cyan
(8) becomes 0 while every non-cyan value, including background 0 and distractor
colors, becomes red (2).

I implemented that cellwise rule directly. The second training example is the
key diagnostic: nonzero distractors on lattice lines disappear, while interior
distractors become red. This rejects both “detect currently all-zero separator
lines” and “preserve unknown colors” alternatives.

Remaining uncertainty before checking: none about grid dimensions or palette;
the rule is coordinate-based and applies independently to every cell.
