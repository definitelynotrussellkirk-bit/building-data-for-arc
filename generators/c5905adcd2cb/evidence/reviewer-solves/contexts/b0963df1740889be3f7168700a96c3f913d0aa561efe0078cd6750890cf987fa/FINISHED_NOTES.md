# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure declaration before revision 1

I had already read and worked on this task's generator and canonical semantics before this required exposed solve, so this is **not blind**. During the solve phase itself I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solutions, or private labels.

## Revision 1

Visible hypothesis: the gray 5 rows/columns divide the 11×11 board into a 3×3 array of 3×3 interiors. The unique yellow 4 sits inside one source interior. Rounding its row/column down to a multiple of four locates that source. Its local position inside the source—local row and local column, each 0..2—selects the destination interior in the 3×3 macro-grid.

Evidence from the examples:

- Example 0 has marker `(6,6)`, source origin `(4,4)`, and local code `(2,2)`. The source's five colored cells reappear at identical offsets in the bottom-right interior.
- Example 1 has marker `(9,4)`, source origin `(8,4)`, local code `(1,0)`. Its three-cell pattern moves to the middle-left interior.
- Example 2 has marker `(8,1)`, source origin `(8,0)`, local code `(0,1)`. Its five-cell pattern moves to the top-middle interior.

The output preserves every gray separator, clears all other prior content, and copies every nonzero/non-gray source cell—including yellow 4—at the same 3×3-local offset in the decoded destination. I implemented this directly. The main rejected alternatives were transposing the local coordinates and preserving background distractors; examples 0 and 1 visibly distinguish both.
