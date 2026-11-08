# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Observed that every demonstration contains exactly one non-background color split into two 4-connected components: a one-cell marker near the top and a larger shape elsewhere. The output is the tight bounding-box crop of the larger component, retaining its color and zero background. Other colors form distractor components but do not have a singleton marker.

Implemented a generic 4-connected component scan. It selects a color having both a singleton component and a non-singleton component, chooses the larger component, and crops it. If more than one color ever matches, the topmost singleton is used as the marker tie-breaker. Expected queries: query 0 returns the lower-left color-6 L-like component; query 1 returns the color-1 3x2 component.

Before implementation, an inline visible-example assertion failed at the supplied `NotImplementedError`, confirming the test exercised the missing behavior. No generator, Racket rule, private labels, prior solutions, or audit evidence were opened.
