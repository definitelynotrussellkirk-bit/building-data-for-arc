# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: yes. I had already reviewed this task's rule and generator before this required post-repair solve, so this is not blind. During this solve I used only the visible examples printed by `solve_episode.py prepare` and did not reopen the generator, Racket source, reference solutions, or private labels.

Visible-example hypothesis: identify every 4-connected component of orange cells (color 7). If any cell in that component lies on the outer grid border, recolor the entire component green (color 3). Leave interior orange components and non-orange distractors unchanged. Evidence: train 0 changes the orange component touching the top edge while preserving the interior component; train 1 changes two separate orange components touching the right and bottom edges while preserving interior orange and a border blue distractor; train 2 changes bottom/left-touching orange components while preserving an interior orange component and the top-border azure distractor.

Implementation probe: breadth-first search over 4-neighbor orange components, track whether each reaches row 0, row H-1, column 0, or column W-1, then recolor all cells of only those components. The output shape is unchanged. Remaining uncertainty is limited to whether diagonal adjacency should count, but the examples support 4-connectivity and the ARC object convention used in the visible patterns.
