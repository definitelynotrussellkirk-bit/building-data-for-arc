# Blind solve notes — 7e52d15790d7

This is a human-visible work log based only on `challenge.json`.

## Observation

Each training input contains three separated monochrome objects on a zero background. The output is not a spatial crop of the whole scene: it is a new strip made from the three tight object crops, top-aligned, with exactly one zero column between adjacent crops.

The output order matches decreasing **bounding-box area**:

- example 2: plus `3×3`, rectangle `2×3`, square `2×2`;
- example 3: diagonal `3×3`, small T `2×3`, line `3×1`;
- example 1: two `2×3` crops before the `2×2` crop.

The only visible tie is example 1's two `2×3` crops. The source's rightmost tied object appears first, so I use rightmost source column as the tie-break. Bottom row is a final deterministic tie-break not evidenced by the examples.

## First hypothesis and implementation

1. Find every 4-connected nonzero same-color component.
2. Extract its tight rectangular crop, preserving zeros inside the crop.
3. Sort by descending bounding-box area, then descending source right edge.
4. Top-align the crops and concatenate them with one zero column.

Predicted test ordering:

- test 1: color 9 (`2×3`, rightmost), color 4 (`3×2`), color 1 (`2×2`);
- test 2: color 4 (`3×3`), color 2 (`2×3`), color 6 (`2×2`).
