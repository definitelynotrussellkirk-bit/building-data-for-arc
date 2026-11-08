# Visible-only solve notes

## Evidence from the four training pairs

- Cells with value `9` act as location markers and disappear in the output.
- The remaining nonzero cells form one colored template. Its bounding box may start away from `(0, 0)` and may contain holes or multiple colors.
- The output keeps the template at its original position.
- For every `9`, the complete template is copied with the marker as the template bounding box's top-left anchor.
- All other cells are zero.

## Competing hypotheses checked against visible examples

1. **Copy only one color:** rejected by training pair 4, whose copied template preserves colors 6, 8, and 7.
2. **Always move the source template to `(0, 0)`:** rejected by training pairs 3 and 4, whose source templates remain offset.
3. **Keep marker cells underneath copies:** rejected by training pair 2, where a marker aligns with a hole in the copied template and becomes zero.
4. **Use only the first marker:** rejected by examples with two or three marker locations.

## Chosen transformation

Construct a zero grid of the same shape. Find all cells whose values are neither 0 nor 9; take their bounding-box top-left as the source anchor and store each colored cell as an offset/value triple. Stamp those triples at the source anchor and at every input cell equal to 9.
