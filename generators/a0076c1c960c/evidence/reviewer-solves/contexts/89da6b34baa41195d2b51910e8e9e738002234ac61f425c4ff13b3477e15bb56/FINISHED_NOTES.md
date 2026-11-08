# Solve work log

## Exposure and policy

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit evidence, or any earlier explanation before solving. I used
only the prepared visible examples and `challenge.json`.

## Revision 1 — horizontal interiors

**Observation.** Every nonempty input row has exactly two colored marker cells.
The output is black except for cyan (`8`) cells strictly between those two
columns on the same row. The marker colors and marker endpoints disappear.
Adjacent markers contribute no cyan cells.

Examples supporting the rule:

- Train 0 row 2 has markers at columns 6 and 9 and outputs cyan at 7–8.
- Train 0 row 6 has adjacent markers at 2 and 3 and outputs nothing.
- Train 3 row 0 has markers at 3 and 8 and outputs cyan at 4–7.
- The same rule works whether the endpoints have equal or different colors.

**Alternatives considered.** Keeping the endpoints, connecting vertically,
connecting equal colors only, and using endpoint colors in the output all
conflict with visible examples. Filling from the first to last marker on a row
with more than two markers is unsupported, so the program acts only on rows
with exactly two markers.

**Predicted queries.** Query 0 should paint row 4 columns 2–6 cyan and leave the
adjacent pair on row 6 empty. Query 1 should paint columns 3–4 on row 0 and
columns 2–3 on rows 1 and 3; the adjacent pair on row 4 contributes nothing.

**TDD probe.** Before implementation I ran a script asserting all four public
training pairs. It failed at the existing `NotImplementedError`, confirming the
probe exercised the missing behavior. I then implemented the minimal row-wise
rule and reran the same assertions.

**Remaining uncertainty.** The visible data does not define behavior for a row
with a count other than zero or two nonzero cells. The implementation leaves
such a row black rather than inventing a pairing convention.
