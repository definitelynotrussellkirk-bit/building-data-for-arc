# Solve notes

## Visible-example inference

All three examples use the first row and first column as headers and leave the input interior blank. For each interior location `(r, c)`, the output copies the top header `input[0][c]` precisely when it equals the left header `input[r][0]`; otherwise the cell stays 0. The two header strips are unchanged.

Checks against the examples:
- In training example 1, a row headed 9 receives 9 under both columns headed 9 and remains 0 under headers 7 and 4.
- Rows headed 7 and 4 behave analogously, including repeated header colors.
- Zero headers do not create colored output, consistent with leaving the background 0.

I implemented this equality-table rule directly. No diagnostic or intentionally wrong revision was needed because all visible examples agree and include repeated labels, unequal labels, and zero headers.
