# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Earlier exposure: none. I had not opened this task's generator, rule, answers,
notes, or any assigned-generator source before this attempt.

Hypothesis: the input is three `N x N` panels separated by solid columns. The
first panel is transformed into the second by one of the eight square-grid
symmetries, and the output is the third panel under the same symmetry.

Checks against the visible examples:

- Example 0: left-right reflection maps panel 1 to panel 2; reflecting panel 3
  left-right gives the shown output.
- Example 1: top-bottom reflection maps panel 1 to panel 2; applying it to panel
  3 gives the shown output.
- Example 2: main-diagonal transpose maps panel 1 to panel 2; transposing panel
  3 gives the shown output.

Implementation: split at the two expected solid columns, enumerate all eight
D4 symmetries in a stable order, retain those mapping panel 1 exactly to panel
2, and apply the same indexed transformation to panel 3. Symmetric inputs can
admit several transformations, so the solver accepts that case only when all
matching transformations produce the same panel-3 result.

Remaining uncertainty: a generated puzzle could intentionally use a
non-dihedral mapping or ambiguous first panels whose candidate transformations
disagree on panel 3. The visible examples strongly support the stated rule.
