# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none to this task's rule, generator, notes, solutions, or labels.
I used only the visible examples created by `blind prepare`.

Hypothesis: all nonzero cells form one rigid pattern. The output preserves every
cell value and column, translating the entire pattern downward until its lowest
occupied row touches the final grid row. The observed vertical shifts are +3,
+2, +4, and +1 across the four demonstrations, exactly the remaining distance
from each input's lowest occupied row to the bottom edge.

Probe: compare nonzero coordinate sets before and after each demonstration after
subtracting a single row offset. All relative coordinates, colors, and columns
are unchanged. Alternatives considered were per-column gravity and cropping;
per-column gravity is not needed and could distort shapes, while output dimensions
show that no crop occurs.

Implementation: collect all nonzero cells, compute one vertical shift from the
global lowest occupied row, and write the cells into a zero-filled grid of the
same dimensions. An all-zero input is returned unchanged. Remaining uncertainty:
the examples use background color 0, so the implementation follows that visible
contract.
