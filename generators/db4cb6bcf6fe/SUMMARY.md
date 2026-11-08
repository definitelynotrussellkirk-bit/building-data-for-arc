# db4cb6bcf6fe

Four nonzero colors each mark a sparse four-point object on an exact canonical-size canvas (`9x12` or `10x14`). For each color independently, fill every horizontal segment between that color's cells, then fill every vertical segment in the row-closed result. Normalize the completed shape up to translation. Sort the four objects by color and output a `4x4` equivalence matrix: diagonal `5`, off-diagonal `8` for equal completed shapes, and `0` otherwise.

The reviewed distribution is closure-sensitive. Distinct raw marker sets can complete to the same shape, while every object has the same `3x5` bounding box and completed area `7`. Thus raw-marker equality, bounding-box equality, and area-only equality all fit the canonical demonstrations but fail every ordinary generated case.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Rule hash: `38e335f43e6f`.
