# Solve work log

I had not seen this task's rule, generator, private labels, or prior solution before this blind episode.

## Initial observations

Each visible input has background color 0, one frequent color forming solid rectangular regions, and one sparse third color. The output removes every sparse-color cell. Sparse cells embedded in, at a corner of, or bridging a one-cell interruption between frequent-color regions become the frequent color; isolated sparse cells on the outside remain background.

A local characterization fits all visible changes: inspect only the original grid and replace a sparse-color cell with the frequent nonzero color exactly when at least two of its four orthogonal neighbors already have that frequent color. Otherwise replace it with 0. This explains corner repairs (two perpendicular neighbors), interior repairs, separator bridges (opposite neighbors), and deletion of border specks with only one adjacent filled cell.

## Revision 1

Before editing `solution.py`, I wrote a visible-training regression script at `/tmp/test_blind_solution.py`; it failed with the scaffold's `NotImplementedError`, confirming the test exercised missing behavior. I then implemented the minimal rule above. Color roles are inferred per grid: the most frequent nonzero color is the solid-region color and every other nonzero color is treated as sparse noise. Existing background and solid cells are preserved.

Remaining uncertainty: a hidden lesson could include adjacent sparse cells inside one intended region, where the visible examples do not show whether repaired sparse cells should support one another. I deliberately use only original frequent-color neighbors because that is the simplest rule supported by all visible pairs and prevents chains of exterior noise from growing into shapes.
