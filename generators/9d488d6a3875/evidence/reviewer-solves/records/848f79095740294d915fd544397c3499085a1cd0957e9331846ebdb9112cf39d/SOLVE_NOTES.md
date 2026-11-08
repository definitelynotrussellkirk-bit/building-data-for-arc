# Solve work log

## Exposure declaration before solving

I had not opened task `9d488d6a3875`'s generator, canonical rule, notes,
reference solutions, private labels, audit records, or any prior explanation.
I used only `solve-blind/challenge.json` and the provided solve workspace.

## Revision 1 — connect equal-colour aligned endpoints

### Observation

Every nonzero colour in each visible training input appears exactly twice. The
two cells for a colour share either one row or one column. In the output, all
cells on the inclusive straight segment between those endpoints are recoloured
to that endpoint colour; unrelated cells remain unchanged.

Concrete checks from the visible examples:

- Training 1: colour 7 expands horizontally from `(0,0)` through `(0,7)`, while
  colour 3 expands vertically from `(1,1)` through `(7,1)`.
- Training 2: both colour pairs expand horizontally, with their original
  endpoints included.
- Training 3: colour 9 expands vertically in column 8 and colour 7 horizontally
  in row 3.

### Program

Copy the grid, group nonzero cells by colour, and for every colour with exactly
two aligned occurrences fill the inclusive row or column interval. Leave a
non-aligned or non-pair colour unchanged rather than inventing a diagonal rule.

### Alternatives considered

A bounding-box fill is contradicted by all examples because only a one-cell-wide
line is added. Extending each pair to a border is contradicted by the horizontal
7 segment in training 1, which stops at its second endpoint rather than at the
right edge. Connecting all nonzero cells regardless of colour is contradicted by
the independent segments.

### Remaining uncertainty

No visible example contains crossing segments. The implementation processes
pairs independently, so a later pair would own an intersection. The test inputs
shown do not contain crossings, and the demonstrated rule does not establish a
special crossing colour.
