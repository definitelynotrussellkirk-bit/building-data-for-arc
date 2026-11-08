# Solve work log

## Provenance

I had already inspected the generator and canonical rule while repairing this
assigned task, so this is **not** a blind solve.  During this solve episode I
used only the visible examples in `challenge.json`; I did not reopen the rule,
generator implementation, reference solutions, private query labels, or prior
solution notes.

## Visible evidence and hypothesis

The examples look like noisy constant-color bands.  Train example 0 has strong
vertical bands and its output fills every column with that column's dominant
color.  Train examples 1 and 2 have strong horizontal bands and their outputs
fill every row with its dominant color.

Crucially, train examples 0 and 1 have the **same 13×14 dimensions** but choose
opposite axes.  Therefore dimensions or aspect ratio cannot determine the
operation.  The deciding observable is how many input cells already agree with
the modal color of their row versus their column.

Hypothesis:

1. Compute the mode of each row and each column.
2. Count cells that agree with their row mode and cells that agree with their
   column mode.
3. Select the axis with the larger agreement count.
4. Replace each row/column on that axis by its mode.

I used a deterministic smallest-color tie-break for a line mode.  No visible
line has an unresolved modal tie, so that detail remains low-risk.  I resolve an
overall axis tie toward rows; the visible examples do not exercise an exact
tie.

## Implementation

`solution.py` implements the hypothesis directly and validates rectangular
input.  It does not key on dimensions, palette identities, stripe widths, or
noise count.

## Remaining uncertainty

The visible data do not establish the intended behavior for an exact row-score
versus column-score tie, or for an individual line with multiple modal colors.
Those cases appear outside the shown distribution.  The central axis-selection
rule is strongly supported because same-size training examples require both
orientations.
