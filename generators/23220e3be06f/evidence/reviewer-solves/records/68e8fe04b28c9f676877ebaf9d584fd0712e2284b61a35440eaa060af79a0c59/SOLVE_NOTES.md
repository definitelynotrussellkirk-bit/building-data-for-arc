# Exposed solve notes — 23220e3be06f

## Visible-example hypothesis

The upper-left cell is a command, not part of the motif. I first set that cell to zero, then take the smallest rectangular crop containing the remaining nonzero cells.

The visible examples establish only these two commands:

- `1`: return the crop unchanged.
- `2`: rotate the crop 90 degrees clockwise.

The first and third demonstrations use command 1 and preserve their tight crops. The second uses command 2 and its output is exactly the clockwise rotation of the tight crop.

## Test predictions

Both masked tests use commands demonstrated in the visible examples, so no extrapolation to unseen commands is needed.

- Test 1 uses command 2. Its tight crop is

  ```text
  0 4 4
  2 0 0
  0 0 0
  0 2 0
  ```

  Rotating clockwise gives

  ```text
  0 0 2 0
  2 0 0 4
  0 0 0 4
  ```

- Test 2 uses command 1. Its tight crop is returned unchanged:

  ```text
  0 0 5 5
  5 9 9 5
  5 0 9 0
  ```

## Independence note

This solve was derived from the exposed visible examples only. I did not consult the reference answer or any private labels during this solve. I had previously inspected the generator while performing the assigned generator review, so this is not a blind/no-prior-exposure solve.
