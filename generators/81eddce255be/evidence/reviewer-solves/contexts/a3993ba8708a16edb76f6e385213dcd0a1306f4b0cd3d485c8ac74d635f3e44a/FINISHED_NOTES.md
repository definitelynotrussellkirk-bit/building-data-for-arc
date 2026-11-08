# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Earlier exposure declaration

I had already inspected and repaired this task's generator and canonical rule before this required post-repair episode, so this is **not blind**. During the solve episode itself I did not reopen the generator, Racket source, reference solutions, private labels, or prior solution explanations; I used only the visible examples printed by `prepare`.

## Revision 1

Visible pattern: the top row contains a blue run whose length is 2, 3, then 4. In each corresponding output, the header is erased and the only retained body object has exactly 2, 3, then 4 cells. Color, shape, and location are preserved. The other two body objects are erased.

Hypothesis: count color-1 cells in row 0 as `K`; find same-color four-connected components below row 0; emit a zero grid containing every component of area `K` in its original place and color. The visible lessons each have a unique match. This predicts query 0 keeps the three-cell color-9 component and query 1 keeps the four-cell color-3 component.

Implementation: breadth-first component extraction, deliberately excluding row 0, followed by an area comparison. I did not use object vertical order, color identity, or shape as selectors.
