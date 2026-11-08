# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — orientation-based recoloring

Earlier exposure before this solve: I had not opened this task's generator, rule,
notes, solutions, audit evidence, or private labels. I had only read the packet's
public workflow directions and the visible examples printed by `blind prepare`.

Hypothesis: every 4-connected blue (`1`) object is a straight line. Recolor a
horizontal blue line yellow (`4`) and a vertical blue line orange (`7`). Objects
already drawn in another color are reference/marker objects and remain unchanged.
This exactly explains all three visible training pairs: each horizontal blue line
changes to 4, each vertical blue line changes to 7, and the 3/8 object is preserved.

Implementation: find each 4-connected blue component independently, classify it by
whether all cells share a row or a column, and recolor only supported straight
components. Preserve an unsupported singleton, bent, or branching blue component
rather than inventing behavior absent from the examples.

Planned probe: run the packet's visible-only blind checker against every training
example and both query executions. Remaining uncertainty is limited to unsupported
non-line blue shapes, which do not appear in the shown data.
