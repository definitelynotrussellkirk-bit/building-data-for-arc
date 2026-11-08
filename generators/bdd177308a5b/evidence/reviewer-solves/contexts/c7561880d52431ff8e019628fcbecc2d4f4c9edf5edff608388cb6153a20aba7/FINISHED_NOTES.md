# Solve work log

Earlier exposure: none. Before this blind episode I did not inspect task `bdd177308a5b`, its generator, rule, notes, solutions, labels, or prior audit records. I used only `solve-blind/challenge.json` and local Python checks.

## Observation and hypothesis

Every grid contains a color-5 L-shaped divider at row 3 / column 3. The nonzero object in the upper-left compartment is a template. Exactly one object elsewhere has the same normalized 4-connected cell coordinates in the same orientation; the output recolors that translated copy to color 5 and leaves the template, rotated/reflected rivals, and unrelated objects unchanged.

I rejected size-only, color-only, and rotation-invariant matching because the visible examples include same-size distractors and rotated/reflected tetrominoes that remain unchanged. The proposed solver finds the divider's strongest row and column, extracts the template above-left of their intersection, compares normalized component coordinates without rotations/reflections, and recolors every exact translated copy outside the template.

## Test-first probe

I wrote `test_visible_examples.py` before implementing `solve`. The first run failed at the `NotImplementedError` in the provided skeleton, confirming the test exercises missing behavior rather than passing vacuously.
