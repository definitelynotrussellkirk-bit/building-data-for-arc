# Solve work log

I had not opened the generator, canonical rule, reference solution, prior solve,
or private labels for `b3750af4dac1`. Before preparation I had only read the
packet-level welcome/return instructions and the assignment text.

## Visible structure and hypothesis

The input is a rectangular array of compartments separated by complete color-1
wall rows and columns. Colors 7 and occasional 9 occur on those walls; colors 2
and 3 occur inside compartments. With `R` compartment rows and `C` compartment
columns, every visible output has length `R*C - 1`, suggesting that the first
compartment is a key and the output has one slot for each remaining compartment.

For every training example, the marked candidate matches the first compartment
on four rotation-invariant quantities:

1. the unordered pair of interior dimensions (so a 90-degree rotation is allowed),
2. the number of color-2 cells,
3. the number of color-3 cells, and
4. the number of color-7 openings on the compartment perimeter.

This distinguishes the marked room from decoys. In particular, training example
2 has another room with the same size and color counts but a different number of
openings, while training example 3 requires swapping height and width. The
positions of the colored cells and openings vary, so I treat them as irrelevant;
color 9 appears only at wall junctions and is ignored.

## Probe

I parsed divider rows/columns as lines containing only `{1, 7, 9}`, enumerated
rooms row-major, and compared the above signature. It produced one candidate in
each training example at room indices 2, 9, and 9 respectively, which maps to
output indices 1, 8, and 8 exactly.

For the two hidden-query inputs, the same rule predicts room 1 for the first
query and room 2 for the second query. No alternate revision was needed before
checking because the visible examples and the decoy analysis agreed.

## Remaining uncertainty

The examples do not prove whether color-9 wall cells could ever be semantic or
whether multiple candidates should all be marked. The visible construction makes
7 the opening color and gives a unique signature match, so the implementation
ignores 9 and marks every exact signature match among the candidates.
