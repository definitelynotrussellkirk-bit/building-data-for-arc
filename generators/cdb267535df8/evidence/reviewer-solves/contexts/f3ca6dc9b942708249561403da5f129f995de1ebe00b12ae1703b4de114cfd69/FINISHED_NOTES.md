# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — geodesic colored Voronoi regions

I had no prior exposure to task `cdb267535df8`, its rule, generator, notes,
solutions, private labels, or audits. I only read the visible examples prepared
in this directory. General packet instructions and ARC design guidance had been
opened before the assignment draw, but they contained no task-specific answer.

Hypothesis: color 5 is an impassable wall. Every nonzero, non-5 cell is a colored
source. For each other cell, compute four-neighbour shortest-path distance to
all sources while avoiding color 5. Fill with the uniquely nearest source color;
if the nearest distance is shared by different colors, leave the cell 0. Ties
between sources of the same color still receive that color. Existing walls stay 5.

Probe: I implemented an independent BFS-per-source scratch calculation against
all three visible training pairs. It matched every output cell (0 mismatches in
all three examples). This also explains the two-cell neutral boundary in train 0,
the larger neutral front in train 1, the enclosed zero pocket in train 2, and the
horizontal tie line in train 2. I found no visible counterexample, so I encoded
that rule directly. Remaining uncertainty is limited to masked-query correctness
and any unseen edge convention not exercised by the visible examples.
