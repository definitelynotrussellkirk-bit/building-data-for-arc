# Post-repair solve notes

This is a human work log. I had already inspected the repaired task during the
generator review, so this is an exposed verification solve rather than a blind
inference record. During this solve I used only `solve/challenge.json` and my
own Python implementation; I did not reopen the generator, Racket source,
private labels, reference solutions, or earlier solution explanations.

## Visible-example observations

- Every input has one bottom-anchored solid gray (`5`) rectangle, one red (`2`)
  marker, one cyan (`8`) marker, and background `7`.
- In every output, the old red cell becomes background and the old cyan cell
  becomes red.
- A new cyan cell appears on the rectangle's bottom row, immediately outside
  one horizontal edge.
- The chosen edge is opposite the original red marker's horizontal side.
- Example 3 places red at the integer midpoint column and stamps on the left,
  so the midpoint belongs to the right/non-left branch.

## Hypothesis

Let `left..right` be the gray rectangle's column span and
`midpoint = floor((left + right) / 2)`. If the original red column is strictly
less than `midpoint`, stamp cyan at `right + 1`; otherwise stamp at `left - 1`.
Move red to the original cyan location and erase the original red.

## Checks before submission

- Training example 1: red is strictly left of midpoint, so the new cyan is to
  the rectangle's right; matches.
- Training example 2: red is right of midpoint, so the new cyan is to the left;
  matches.
- Training example 3: red equals midpoint, so the strict comparison selects
  the left destination; matches and fixes the tie convention.
- Training example 4: red is on the right, so the new cyan is left; matches.
- Both test inputs leave an in-bounds cell on the derived destination side.

No alternative survived all four visible examples, so I submitted this as the
first solve attempt rather than manufacturing a negative revision.
