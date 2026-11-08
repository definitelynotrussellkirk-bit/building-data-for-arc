# Solve work log

## Initial exposure

Before this solve I had not opened the assigned task's generator, rule, notes,
reference solution, private labels, or any source for the main repair target. I
used only the visible examples printed by `python3 review.py blind prepare` and
the generated solve-lane files.

## Revision 1 — connected-compartment color propagation

**Hypothesis.** Color 5 is a wall system. If 5-cells are treated as blocked,
every 4-connected non-5 compartment contains exactly one nonzero/non-5 colored
seed. The output replaces all background 0 cells in that compartment with the
seed color while preserving every wall cell. Internal wall cells can make an
irregular component, so the operation is a flood fill rather than merely filling
axis-aligned rectangles.

**Evidence from visible pairs.** In training example 1, the compartment carrying
color 9 contains an interior wall at row 6, column 5, yet cells on both sides are
filled because they remain connected through the row above. All other visible
regions follow the same rule, including one-cell-wide compartments.

**Implementation.** Enumerate 4-connected components of cells whose value is not
5, collect their seed colors, and fill the component when exactly one seed is
present. An ambiguous component is left unchanged instead of guessing.

**Remaining uncertainty.** The visible data does not show a component with zero
or multiple seeds. The conservative fallback should not affect the presented
instances.
