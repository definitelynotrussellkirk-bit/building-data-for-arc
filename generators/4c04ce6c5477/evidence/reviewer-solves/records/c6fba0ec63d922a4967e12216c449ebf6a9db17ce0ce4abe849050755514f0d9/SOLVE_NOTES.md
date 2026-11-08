# Solve work log

Earlier rule exposure exists from the generator-repair phase and from a prior solve bound to an older generator hash. During this fresh solve phase I consulted only `solve/challenge.json` and wrote the program below from the visible pairs; I did not consult the Racket source, generator source, private labels, reference solutions, or the retained prior solve files.

## Hypothesis

Each input contains separated monochrome objects on background 0. The output is a one-row list of object colors ordered by descending **bounding-box height**:

- Train 1: heights are color 7 = 5, color 1 = 4, color 5 = 3, producing `[7,1,5]`.
- Train 2: heights are color 3 = 3, color 2 = 2, color 6 = 1, producing `[3,2,6]`.
- Train 3: heights are color 2 = 5, color 6 = 4, color 1 = 3, producing `[2,6,1]`.

This also explains why area and left-to-right order do not work consistently. I implemented four-neighbor same-color component extraction, measured each component's row span, sorted height descending, and returned the colors in a 1×N row. Left edge and color are deterministic tie-breakers, although the visible examples have distinct heights.
