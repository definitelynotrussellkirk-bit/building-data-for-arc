# Final-source visible-only solve notes

## Visible evidence

The three demonstrations preserve colors and layout while doubling both dimensions. Each input cell becomes a solid 2×2 block: values are duplicated horizontally, and each expanded row is duplicated vertically. This holds for both 3×3 and 4×4 examples and for repeated/background-heavy regions.

## Hypothesis

Apply nearest-neighbor enlargement by factor two to the complete rectangular grid.

## Competing interpretations rejected

- Whole-grid 2×2 tiling would repeat complete rows and columns rather than form local 2×2 blocks.
- Repeating each whole row twice horizontally would put the first source value again halfway across the output.
- Transposing before enlargement would change asymmetric positions.
- Conditioning on the public size/palette profile is unnecessary: these visible examples include neighboring palette counts yet exhibit the same cellwise law.

## Implementation

Duplicate every value twice inside its row, then duplicate each expanded row twice. The implementation is shape-generic and color-agnostic. No revision was needed before the first visible check.
