# Blind solve notes — d8b498586958

## Visible structure

Each input has a two-row header containing one `5`, then a full `9` separator,
an `n x n` binary picture in color `2`, another full `9` separator, and an
`n x n` binary picture in color `6` (the test instance uses `7`).  The output is
an `n x n` picture in color `8`.

## Hypothesis

The corner occupied by `5` selects a Boolean operation applied cellwise to the
two pictures:

- top-left: union / OR (training example 3)
- top-right: intersection / AND (training example 4)
- bottom-left: symmetric difference / XOR (training example 1)
- bottom-right: first picture minus second / `A AND NOT B` (training example 2)

I verified each claimed operation against every cell of its corresponding
visible example.  The changing lower-picture color (`6` in training, `7` in
test) appears to be a role color rather than a semantic change, so the code
uses nonzero membership in the lower picture.

## First implementation

Parse the two square pictures by width, read the marker corner, apply the
selected Boolean predicate cellwise, and emit `8` for true and `0` otherwise.
No reference rule, generator, private label, prior solution, or audit material
was consulted.
