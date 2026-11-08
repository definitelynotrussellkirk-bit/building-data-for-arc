# Solve work log

I had earlier exposure to the task's rule while repairing the generator, so this is an exposed post-repair solve, not a blind solve. During this episode I used only the visible examples in `challenge.json`; I did not reopen the generator, Racket source, reference solutions, or private labels.

## Revision 1

**Hypothesis.** The nonzero color is a rectangular frame with one side interrupted by a single mouth gap. Yellow (4) pours from the outside through every line aligned with the gap, fills the cavity as far as the opposite closed wall, fills the cavity and one outside cell on each arm-tip line, and continues beyond the two tips as 45-degree diagonal spouts. Cells behind the solid portions of a long arm remain unchanged; train example 2 shows that distinction below its lower tip.

**Implementation.** Infer the shape color and bounding box, identify the only incomplete side, and derive the two tip positions from the contiguous missing run. Apply the same coordinate rule in all four orientations, painting only zeros. Diagonal points outside the canvas are clipped.

**Checks to make from the examples.** Train 0 exercises a bottom opening with 2/2 arms; train 1 a left opening with 1/1 arms; train 2 a left opening with asymmetric 1/3 arms. Together they distinguish the actual tip positions from a fixed-arm-length rule and clarify that only tip lines—not every row/column behind an arm—receive cavity fill.

**Remaining uncertainty.** None for the displayed grammar; the code assumes one rectangular frame, one contiguous mouth gap, background 0, and fill color 4, exactly as all visible examples show.
