# Visible-only solve notes

I used only the prepared examples shown in this solve episode. Earlier in the
review I had seen the assigned rule, so this is an exposed post-repair solve,
not a blind solve; I did not reopen the generator, Racket rule, reference data,
or private labels after preparation.

The visible examples support one consistent transformation. Exactly one pair of
opposite borders is solid and has two colors. Each color-1 marker is preserved,
and one adjacent cell is painted on the side facing its nearer/matching border:
for top/bottom borders, markers in the first half paint one cell upward with the
top color and markers in the second half paint one cell downward with the bottom
color; left/right is analogous. The 13-column vertical example includes a
marker at column 6, showing the exact odd-axis middle belongs to the first/left
side (`2 * coordinate < extent`).

The implementation detects which opposite border pair is solid, copies the
input, then applies that one-cell projection to every marker. The first natural
implementation is submitted without a diagnostic or intentionally wrong probe
because all three demonstrations already distinguish orientation, side, and the
odd-axis tie.
