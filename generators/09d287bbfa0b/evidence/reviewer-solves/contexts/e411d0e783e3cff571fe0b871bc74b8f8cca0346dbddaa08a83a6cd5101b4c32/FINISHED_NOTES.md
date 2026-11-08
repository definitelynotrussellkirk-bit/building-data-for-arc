# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, notes, reference solution,
private labels, or any generator/rule material for the assigned repair.  I used
only the visible examples in `challenge.json`/`README.md` and local Python.

## Hypothesis

Each puzzle contains background color 7 and a long horizontal/vertical cross of
another color.  Off-cross colored marks are reflected across both arms of the
cross, while the cross itself is protected.  Each source mark can therefore
create up to three in-bounds copies: across the horizontal arm, across the
vertical arm, and across both.

Visible example 1 resolves an important edge case.  The marks at `(1,5)=3` and
`(3,5)=4` lie opposite one another around the horizontal arm.  The output has
`(1,5)=4` and `(3,5)=3`, so the transformation uses a snapshot and writes mirror
positions rather than merely filling blank cells.  A colored mark embedded in
the divider row stays where it is, so divider cells are excluded from copying.

## Implementation and probe

I detect the background as the modal color.  Among the other colors, I select
the row/column pair with the largest combined same-color support; this tolerates
the one visible divider interruption.  I then traverse a snapshot in row-major
order and write each off-cross, non-background value to every in-bounds reflected
position.

Before implementation, `/tmp/test_blind_visible.py` imported the supplied
skeleton and failed with `NotImplementedError` (receipt:
`checks/session/blind-visible-red.log`).  After implementation I used the same
probe against all visible training pairs.

## Alternatives and remaining uncertainty

A weaker alternative was to fill only background cells, but that contradicts
the color exchange in visible example 1.  Another alternative was to force each
reflection orbit to one color, but the same example's output is not globally
symmetric.  The remaining uncertainty is conflict order if several different
source colors target the same cell through different mirror transforms; the
visible examples support snapshot-based row-major writes.
