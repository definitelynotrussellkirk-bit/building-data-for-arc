# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 0 — harness baseline (diagnostic probe)

Earlier exposure to task `cc4d8d3dc442`: none known. I have not opened its
source, reference rule, private labels, prior notes, or review records.

Visible structure: color 5 partitions each 11×11 grid into 4-cell-wide
connected regions; color 2 marks some cells. The provided output preserves the
5-walls, turns every unmarked region to 0, and fills every marked region
uniformly. I first ran the untouched `NotImplementedError` stub only to verify
that the episode checker catches an unimplemented solver before I rely on it.
This is an execution diagnostic, not a proposed puzzle rule.

## Revision 1 — connected-region marker parity

I enumerated 4-neighbor components of cells not equal to 5 in each visible
training input. For every component, I compared its area, bounding box, number
of 2-cells, and output color:

- Unmarked components (zero 2s) become all 0.
- Components with an even positive number of 2s become all 7.
- Components with an odd number of 2s become all 8.
- Color-5 walls remain unchanged.

The examples deliberately do not mix odd and even marked components within one
training grid, so a weaker global-parity rule also fits the demonstrations.
The first query contains marker counts 4, 3, and 3 across its marked regions,
which appears designed to distinguish that shortcut. I therefore apply parity
independently to each connected region. The second query has counts 3, 3, and 1,
so all of its marked regions should become 8. Remaining uncertainty is limited
to the local-vs-global parity ambiguity; local parity is the more compositional
rule and makes the first query diagnostically useful.
