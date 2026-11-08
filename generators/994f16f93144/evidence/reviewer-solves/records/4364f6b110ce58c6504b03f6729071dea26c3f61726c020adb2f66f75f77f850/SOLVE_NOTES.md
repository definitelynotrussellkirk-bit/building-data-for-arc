# Solve work log

## Exposure and constraints

I had not seen task `994f16f93144`, its generator, its Racket rule, private query
labels, reference solution, notes, or prior solve explanation before this blind
solve. I used only the visible examples prepared in this directory and local
experiments against those examples.

## Revision 1 — maximal same-colour diagonal runs

**Observation.** In example 0, each length-three diagonal has its middle cell
recoloured to 8. Example 1 resolves two ambiguities: the four-cell diagonal has
both interior cells recoloured, while the vertical run of three 9s is left
unchanged. Example 2 repeats length-three and length-four diagonals in the other
diagonal orientation. Thus the operation is not “change one midpoint,” and it is
not applied to horizontal or vertical lines.

**Hypothesis.** For every maximal contiguous 45-degree diagonal run of one
nonzero colour with length at least three, retain the two endpoints and recolour
all interior cells to 8. Find all runs from the original input before recolouring,
so a crossing cannot affect detection of another run.

**Alternatives rejected from visible evidence.** Recolouring the middle cell only
fails on the length-four runs. Applying the rule to all straight orientations
would alter the vertical 9 run in example 1. Recolouring every member of a line
would alter endpoints that remain unchanged in every example.

**Probe.** I wrote a local test that loads all visible train pairs from
`challenge.json`. Before implementation it failed with `NotImplementedError`.
After implementing the two diagonal directions, the same test passed all three
visible examples. I then used the official visible-only check.

**Remaining uncertainty.** The demonstrations do not show intersecting eligible
runs or a pre-existing colour 8. The implementation detects every run against a
frozen input and unions the marked interior coordinates, which is the most direct
extension of the observed rule.
