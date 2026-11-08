# Solve work log

## Exposure declaration

I had seen the task rule during the preceding generator review, so this is an
**exposed** solve. After `prepare`, I consulted only `solve/challenge.json`, this
work log, and my own solution code; I did not reopen the generator, Racket rule,
reference solutions, private labels, or the preserved earlier solve.

## Revision 1 — unique cyan-free block as macro-template

All three visible inputs are 11×11 grids split by gray-5 separator rows and
columns into nine 3×3 blocks. In each demonstration exactly one block contains
no cyan-8 cells. Its nine values match the output at macro scale: source cell
`(i,j)` becomes a solid 3×3 output block at macro-position `(i,j)`, while the
separator lines remain gray-5.

I implemented that rule directly: enumerate the nine blocks, require exactly one
without 8, preserve the separators, and broadcast each selected template cell
over its corresponding 3×3 output region. This is a genuine solve revision; I
did not add an intentional negative. Remaining uncertainty is limited to the two
masked queries, since the check command reports only visible demonstrations and
execution behavior.
