# Blind solve notes — c5905adcd2cb

This is a human work log based only on `challenge.json`.

## Observations

- Each 11×11 input is partitioned by solid color-5 rows and columns into a 3×3 array of 3×3 panels.
- Every output preserves the dividers, clears eight panels, and retains one complete 3×3 pattern.
- The retained pattern is copied from the unique input panel containing color 4:
  - training 1: source panel (2,2), color 4 at local (0,1), output panel (0,1);
  - training 2: source panel (1,0), color 4 at local (0,2), output panel (0,2);
  - training 3: source panel (2,0), color 4 at local (1,2), output panel (1,2).
- Thus the color-4 cell is both part of the payload and a local coordinate naming the destination panel.

## Hypothesis

Locate the panel containing color 4. Copy that entire panel to the panel whose
row/column indices equal the marker's row/column inside the source panel. Erase
all other non-divider cells.

## Test-instance predictions

- Test 1: source panel (1,0), local marker (0,2) ⇒ copy it to panel (0,2).
- Test 2: source panel (0,0), local marker (2,0) ⇒ copy it to panel (2,0).

## Implementation choices

The solution infers solid nonzero divider rows/columns instead of hard-coding
indices 3 and 7, preserves those divider cells exactly, and checks that source
and destination panel shapes agree. No reference rule, generator, private label,
or prior explanation was consulted.
