# Solve work log

## Prior exposure

Before this solve I had already inspected the selected generator and canonical Racket rule while repairing the task, so earlier rule exposure is **yes**. During this solve phase I did not reopen the rule, generator, reference solutions, private query labels, or prior solution explanations. I used only the visible examples in `solve/README.md` / `solve/challenge.json` and my own Python.

## Visible-example hypothesis

Each input contains one non-gray colored object and one or more solid gray (5) rectangles. The colored object defines a rectangular template by its complete bounding box. The outputs copy that entire crop—including any background-zero holes—into the top-left corner of every gray connected component. Gray cells outside the copied crop remain gray. The original colored object is unchanged.

Evidence from the visible pairs:

- Example 0 has a 4×2 source crop and 6×2 gray targets. The top four rows of each target become the source pattern, while the bottom two rows stay gray.
- Example 1 has a dense 3×4 source and 3×4 targets, so each target is fully replaced.
- Example 2 has a 5×2 source crop and 5×4 targets. The first two target columns receive the crop and the two surplus columns remain gray. Source-background zeros inside the crop overwrite gray, which rules out copying colored cells only.

## Implementation

I locate all cells whose values are neither 0 nor 5, take their global bounding box as the source template, find four-connected gray components, and copy the complete template crop at each component's top-left corner. I preserve the rest of the input grid. The two query inputs satisfy the same object/target structure.

Remaining uncertainty is limited to inputs outside the demonstrated domain, such as multiple colored sources or malformed/nonrectangular gray regions; the prepared queries do not show those cases.
