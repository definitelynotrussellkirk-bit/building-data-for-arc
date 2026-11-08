# Exposed visible-only solve work log

This is a contemporaneous assistant work log, not a captured token-level transcript or a blind discovery. I had already authored and reviewed the generator and read its rule before this episode. That prior knowledge remains in memory. Since preparation I have read only the public challenge and my own new solution; I have not consulted generator code, Racket source, reference solutions, previous explanations, or private labels. No authoring helper is imported by the solver.

## Visible observations and hypothesis

Example 0: input 12x20; output 3x4. The output is the color-4 component's crop recolored to 8. Its row counts are (1,4,1), matching blue, while its column counts are (1,3,1,1), matching red. The blue/red shapes themselves have different pixel arrangements.

Example 1: input 15x20; output 3x4. The selected component is color 6, so fixed color 4 does not explain all demonstrations. The selected rows are (2,3,1) and columns (1,2,2,1). The color-4 alternative has the right row counts but different ordered column counts, so rows alone do not suffice.

Example 2: input 12x20; output 4x3. Color 6 appears in two separated components, so components must be found by same-color edge connectivity instead of merging all cells of one color. The selected color-4 component has rows (1,1,3,1) and columns (3,2,1), matching the respective anchors. The exact crop preserves internal zero cells and its own dimensions.

The attempted rule is therefore: split nonzero pixels into monochromatic four-neighbor components, take blue's ordered row counts and red's ordered column counts, find the other component matching both, crop that actual component, and recolor its occupied pixels to 8. The visible examples each have one matching target. Components are sorted spatially for deterministic behavior outside that observed case.

## Implementation and limits

`solution.py` is a fresh standalone flood-fill implementation with no shared task imports. It preserves the input and compares full ordered count tuples, including their lengths. I am submitting one genuine solution attempt; I have not fabricated a failed revision or an intentional teaching negative.

Query 0: input 11x21; output unknown. Query 1: input 12x15; output unknown. Visible feedback and successful execution cannot establish hidden-query correctness. I will stop if the visible examples pass and both queries execute, while reporting hidden correctness as withheld.
