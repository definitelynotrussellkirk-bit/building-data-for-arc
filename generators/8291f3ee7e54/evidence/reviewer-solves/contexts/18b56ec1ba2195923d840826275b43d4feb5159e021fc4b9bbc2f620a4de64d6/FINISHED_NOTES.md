# Blind solve notes — 8291f3ee7e54

## Observation

Each input contains one hollow square at each of several side lengths. Shapes can overlap (later colors visibly replace pixels at crossings), and one test square is clipped by the canvas. The outputs discard the original positions and place the same square outlines concentrically.

Across the visible examples, side lengths descend by two. The largest square becomes the output boundary; each smaller square is centered inside it. A 3×3 outline leaves a zero center, while a 1×1 or 2×2 object naturally fills the center.

## Hypothesis implemented

1. Group nonzero cells by color.
2. Infer a square's side as the larger of its row-span and column-span. This survives the visible overlaps and the left-clipped 9×9 test square, whose height remains nine.
3. Make a square canvas the size of the largest inferred square.
4. Draw each color's hollow perimeter at centered offset `(outer_side - side) // 2`.

No generator, Racket rule, private labels, prior solution, or audit record was consulted.

## Limit

A square clipped on both axes so severely that neither visible span equals its intended side would need sequence-based extrapolation. No visible example requires that extrapolation.
