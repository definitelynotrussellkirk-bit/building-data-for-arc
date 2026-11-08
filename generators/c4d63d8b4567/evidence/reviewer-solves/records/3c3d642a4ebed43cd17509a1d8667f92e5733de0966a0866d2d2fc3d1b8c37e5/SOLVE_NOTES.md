# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none to this task's rule or implementation. I only read the visible
examples prepared in this folder.

Hypothesis: each nonzero colour supplies marker cells. Whenever two markers of the
same colour share a row or a column, fill the inclusive straight segment between
them. Markers without a same-colour collinear partner remain unchanged. This fits
all four examples, including colour 5 in example 3: its row-5 pair is connected,
while the extra marker at (4,5) remains isolated.

Implementation: collect nonzero coordinates by colour, inspect every pair, and
paint horizontal or vertical spans. The pairwise form intentionally supports
more than two markers and multiple independent spans without guessing a special
pairing rule.

Remaining uncertainty: examples do not show crossing segments of different
colours. The implementation processes colours in encounter order, so a crossing
would be overwritten by the later colour. No crossing is present in the visible
lesson or queries; I did not invent an unsupported tie-break rule.
