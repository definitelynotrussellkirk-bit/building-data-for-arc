# Post-repair visible solve notes

This solve is **not blind**: I had already inspected and repaired the assigned generator before this required post-repair exercise. During the solve itself I used only the visible examples printed by `review.py solve prepare`; I did not reopen or consult the Racket authority.

## Visible inference

The 5x11 input divides into two aligned 5x5 binary panels at columns 0–4 and 6–10, with column 5 blank. The 5x17 output divides into three 5x5 panels at columns 0–4, 6–10 and 12–16.

Comparing corresponding coordinates across the visible examples:

- output panel 1, color 2: occupied when either input panel is occupied (union);
- output panel 2, color 3: occupied only when both are occupied (intersection);
- output panel 3, color 4: occupied when exactly one is occupied (exclusive-or).

I implemented those three cellwise predicates directly. The visible examples include all four occupancy states (00, 10, 01, 11), so the order and XOR semantics are identifiable without consulting a reference.
