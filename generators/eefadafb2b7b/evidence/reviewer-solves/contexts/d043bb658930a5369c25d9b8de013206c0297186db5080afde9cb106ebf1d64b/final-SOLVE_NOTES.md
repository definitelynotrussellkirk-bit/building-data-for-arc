# Fresh solve notes

## Visible-example hypothesis

The input contains two red `2×2` blocks and scattered cyan cells. The scalar output appears to ask whether a **single cyan component** reaches the one-cell neighborhood around both red blocks.

The first positive demonstration requires diagonal connectivity, so cyan components must be 8-connected rather than 4-connected. The negative demonstrations show that merely having cyan near each block, or having a component whose bounding box spans the blocks, is insufficient. The third positive demonstration suggests that the bridging component need not be the largest cyan component.

## Implemented rule

1. Find the two all-red `2×2` windows.
2. Flood-fill cyan (`8`) cells with all eight neighbor directions.
3. For each component, test whether at least one cell lies in the one-cell ring around each red block.
4. Return `[[8]]` if one component touches both rings; otherwise return `[[0]]`.

No reference source was consulted during this solve. I had already seen the rule while reviewing the generator, so this is not a blind solve and will be marked as earlier exposure.
