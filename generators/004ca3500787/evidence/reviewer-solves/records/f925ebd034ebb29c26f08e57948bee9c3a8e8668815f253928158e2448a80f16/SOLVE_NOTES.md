# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure and scope

Earlier exposure: yes. Before this new episode I repaired this task's generator
and inspected its rule. During this episode I have read only this freshly
prepared challenge and its README; I have not opened generator or reference
source, prior solution code or explanations, or private query labels.
This is an exposed-rule solve, not an independent blind inference result.

## Revision 1

The four visible examples contain separated red components. Repeated shapes
can occur in different orientations, while the output depicts the unique shape
in cyan in a tight rectangle. Examples include same-size shape distinctions
and a differently sized singleton. The shown output orientations agree with
the lexicographically least normalized coordinate list across rotations and
reflections.

I wrote a fresh standard-library solver: flood-fill red four-connected
components, classify each across the eight square symmetries, select the class
with frequency one, and render that canonical pose in cyan. It does not use
component position, input dimensions, sample index, or any generator imports.

Planned check: run the official visible-example checker once on this revision.
Private-query correctness remains unknown and is not used for stopping.
