# Solve work log

I had not inspected task `97bcb3b9194e`'s generator, Racket rule, private labels, prior solutions, or audit records. The first preparation process took longer than the shell call and was allowed to complete separately; I then used only the generated public `challenge.json`.

## Revision 1

Each input decomposes into solid nonzero rectangular objects on a zero background. Most cells inside an object use color 1; colors 4 or 6 are sparse markers. In every visible example, two objects have the same bounding-box shape. One member of that repeated-shape pair has the same number of marker cells as the differently shaped object; the requested output is the other member of the repeated-shape pair, whose marker count is unique.

I implemented 4-connected component extraction, crops each component, treats its modal color as fill, and counts non-fill marker cells. It selects a component whose shape repeats but whose marker count occurs once. The public queries expose an uncertainty not resolved by the examples: query 1 contains two repeated shape families and therefore two candidates under the visible rule. I used the larger-area repeated family as a deterministic tie-break because it preserves the main repeated-object structure and selects a single crop. This tie-break is a guess; an alternative is the smaller family or returning multiple odd objects, but the visible examples provide no evidence for output composition in that case.
