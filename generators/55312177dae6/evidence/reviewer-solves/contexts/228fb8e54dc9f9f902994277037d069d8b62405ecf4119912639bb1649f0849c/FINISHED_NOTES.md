# Solve work log

## Exposure

I had not seen task `55312177dae6`, its generator, its rule, private labels, or prior solutions before this solve. I used only the visible examples in `challenge.json` and small local analyses of their connected components.

## Revision 1 — repeated shape modulo rotation

Hypothesis: split the input into nonzero 4-connected components. Exactly one component shape occurs at least twice up to rotation; the other objects are distractors. Return the repeated shape, recolored 8, in a canonical orientation.

Probe: I listed each component's cropped bitmap, area, bounding box, and four rotations for all visible examples. The repeated classes were:

- example 0: two chiral L tetrominoes;
- example 1: two T pentominoes;
- example 2: two L triominoes;
- example 3: two opposite-chirality L tetrominoes.

Each expected output belongs to the repeated class. Reflections must not be treated as equivalent: example 0 contains an opposite-chirality L distractor.

Orientation rule inferred from all examples: choose the rotation with the fewest rows (widest presentation). If several rotations have the same dimensions, choose the row-major bitmap with occupied cells earliest, which makes the result top-heavy and then left-heavy. Recolor occupied cells from 1 to 8.

Remaining uncertainty: the visible data uniquely supports rotation equivalence, but the canonical-orientation tie-break is inferred from only square T/L examples. The implementation is deterministic and reproduces all four visible outputs.
