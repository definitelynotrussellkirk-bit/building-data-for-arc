# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — diagonal-plus-axis parallelogram

Earlier rule exposure: none. I only read the public challenge prepared in this
folder.

Observation: each input has two azure (8) cells. The green output is the outline
of a parallelogram having those cells as opposite corners. Decompose the endpoint
displacement into (a) the longest possible 45-degree diagonal vector and (b) the
remaining horizontal or vertical vector. The four translated copies of those two
vectors exactly explain all three demonstrations. For example, a displacement of
(+7,+4) becomes (+4,+4)+(+3,0); a displacement of (+7,-11) becomes
(+7,-7)+(0,-4).

I considered a generic bounding box and a shortest-path corridor, but both fail:
the slanted edges in the demonstrations are always 45 degrees, and the residual
axis-aligned distance appears on two opposite sides rather than as a single path.

Probe: `/tmp/test_blind_solution.py` imports the solution and compares all three
visible training outputs. Before implementation it failed at the untouched
`NotImplementedError`, establishing the test's red state. The implementation
copies the grid, finds exactly two 8-cells, constructs the two component vectors,
and draws the four inclusive edges while preserving nonzero endpoint colors.
Remaining uncertainty: degenerate collinear or perfect-diagonal endpoint pairs
are not demonstrated; the implementation treats them as a collapsed
parallelogram and draws the direct segment.
