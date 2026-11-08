# Blind solve notes

The examples separate nonzero cells into 4-connected objects. The output keeps
interior objects orange (7), keeps objects that occupy a grid corner orange, and
changes an orange object to green (3) exactly when the object touches one and
only one of the four grid borders. Existing green objects are already-positive
examples and remain unchanged.

Checks against the demonstrations:

- Example 0: the top-only green L and left-only orange L are positive; the
  interior L and bottom+left horizontal line are negative.
- Example 1: the right-only line and bottom-only green line are positive; the
  interior line and top+left domino are negative.
- Example 2: the top-only domino and bottom-only L are positive; the interior L
  and bottom+right vertical line are negative.

Implementation labels 4-connected same-color components, counts distinct grid
sides touched, and recolors only color-7 components with exactly one side.
