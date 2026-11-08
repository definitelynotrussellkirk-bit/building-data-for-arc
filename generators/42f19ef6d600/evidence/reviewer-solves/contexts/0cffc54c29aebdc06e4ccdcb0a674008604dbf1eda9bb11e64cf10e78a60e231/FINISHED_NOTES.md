# Solve work log

## Prior exposure

I had not seen the rule, generator, reference solution, private labels, or prior
solution notes for task `42f19ef6d600`. I used only the visible examples in the
prepared challenge and local Python checks against their public outputs.

## Hypothesis

Orange (`7`) is the background. Each non-orange same-color 4-connected object is
considered separately. Objects with extent in both row and column directions are
made of horizontal and vertical strokes. Every consecutive stroke of length at
least two is extended by one cell at both ends, using blue (`2`), when that cell
is in bounds and is background. A component that is only one row or one column
thick is left unchanged.

This explains the otherwise easy-to-miss cases:

- A solid rectangle receives a complete one-cell orthogonal border.
- A hollow frame receives extensions only where its rows/columns contain runs of
  length at least two; the hole remains untouched.
- The isolated one-row bar in train example 2 is unchanged.
- A 2x2 block receives all eight orthogonal extension cells.

## Probe and implementation

I first wrote a local visible-example test that imports `solution.py` and compares
all three public training outputs. It failed on the untouched template with
`NotImplementedError`, confirming the test exercised the missing solve behavior.
I then implemented same-color 4-connected components, consecutive-run detection,
the two-dimensional component filter, and in-bounds background-only painting.

Remaining uncertainty: the examples consistently fix background `7` and extension
color `2`, so the solution keeps those constants rather than guessing colors from
frequency. The private queries are not consulted.
