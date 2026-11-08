# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none known. I have not opened any generator, rule, reference
solution, prior solve, notes, or audit evidence.

Observation: every training input contains several same-colour connected objects,
but the output is exactly the tight bounding-box crop of the single largest
4-connected nonzero component. The other substantial colour is split into two
smaller components; isolated border cells act as distractors or tags. Component
sizes in the four examples are respectively 7 versus 4, 6 versus 3, 7 versus 4,
and 7 versus 3. This also predicts a 6-cell colour-4 crop for test query 0 and a
7-cell colour-7 crop for test query 1.

Implemented a colour-preserving 4-neighbour flood fill, selected the component
with greatest area, and reconstructed only that component inside its tight box.
A possible alternative is a border-marker/pointer rule, but largest-component
selection explains all visible examples directly and gives the same predictions
for both visible queries. Remaining uncertainty: unseen ties are unspecified.
