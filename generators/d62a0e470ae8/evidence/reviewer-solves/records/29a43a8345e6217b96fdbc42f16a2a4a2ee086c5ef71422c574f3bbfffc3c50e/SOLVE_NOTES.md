# Blind solve notes

Only the public README and challenge.json were read. No earlier rule exposure, generator consultation, reference rule, private labels, audits, or prior solutions.

## Hypothesis

The top-left pixel is a transformation code. Ignore that marker when finding monochromatic objects. Choose the largest component under four-neighbor (orthogonal) connectivity, isolate it on a zero background, and crop to its bounding box. Code 1 rotates the crop clockwise by 90 degrees; code 2 reflects left-right; code 3 reflects top-bottom; code 4 rotates 180 degrees.

The visible examples each cover a distinct code. Example 0 has an isolated extra pixel and its main five-by-two crop is reversed vertically. Example 1 has smaller detached components and its main two-by-five crop is rotated 180 degrees. Example 2 distinguishes orthogonal from diagonal connectivity: the pixel diagonally adjacent at (7,1) is excluded, and the five-pixel main three-by-three object rotates clockwise. Example 3 is a two-by-four object reflected left-right.

## Revision 1 probe

Implement the common component-selection and marker transformation hypothesis without per-example exceptions. Compare all four visible outputs exactly, then execute both queries. The query outputs are predictions; their correctness is unavailable in the visible-only checker.

## Limitations

There is one demonstration per marker, and no visible tie among largest components. Unknown marker codes and equal-size ties are not identified by the demonstrations. The code resolves ties deterministically by discovery order, but this is a fallback rather than an inferred part of the rule.
