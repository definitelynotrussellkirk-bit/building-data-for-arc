# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure declaration

Before this solve episode I had already inspected the task's generator and Racket authority while repairing the assigned source, so this is **not** a clean blind solve. I did not consult the generator, Racket rule, reference solutions, private query labels, or prior solution explanations after `solve prepare`; this revision uses only the visible `challenge.json` examples.

## Revision 1

**Visible structure.** Every input has even dimensions and every output is exactly half the input height and half the input width. Splitting an input at its horizontal and vertical midlines gives four same-sized colored quadrants. At each output coordinate, the output color is selected from the four cells at that same local coordinate.

**Hypothesis.** Treat zero as transparent and overlay the quadrants with a fixed positional priority. Cells in the visible training pairs where several quadrants are nonzero establish the precedence: top-right first, then bottom-left, then bottom-right, then top-left. If all four are zero, emit zero.

**Implementation.** `solution.py` validates a nonempty rectangular even-sized grid, computes the four corresponding quadrant cells for each local coordinate, and chooses the first nonzero value in the order TR > BL > BR > TL.

**Alternatives considered.** A numeric color ordering is incompatible with visible overlaps because selected outputs depend on quadrant position rather than largest or smallest color. Boolean union alone also cannot explain which original color survives an overlap. No rotation, reflection, or row/column movement is needed because each output coordinate corresponds directly to the same local coordinate in all four quadrants.

**Remaining uncertainty before checking.** None material for the visible family; the examples expose all four precedence levels and the transparent all-zero case. I will stop after the first exact check rather than revise around hidden feedback.
