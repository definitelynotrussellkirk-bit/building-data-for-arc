# Visible-only solve notes

Earlier exposure: I reviewed this task's generator before this solve episode, so this is not blind. During the solve phase I used only the prepared visible examples and did not reopen the generator, Racket rule, private labels, reference solutions, or earlier solution explanations.

## Hypothesis 1

Each nonzero cell other than gray `5` is a colored seed. Copy its color into consecutive cells to its right, stopping immediately before the first gray `5`; if no gray lies to its right, continue to the row boundary. Preserve gray cells and all other rows/cells.

Evidence from the visible examples:

- Train 0: row 0's `2` at column 2 fills only column 3 because gray is at column 4; row 3's `9` fills columns 3–5 before gray at column 6; row 1's `4` reaches the border.
- Train 1: row 0's `9` stops before gray at column 6, row 1's `7` reaches the border, and row 6's `6` stops before gray at column 4 despite another gray later.
- Train 2: row 0's `2` reaches the border while row 3's `3` stops at the first gray, not the later gray.

Implementation is shape-agnostic and scans the original row so newly painted cells do not become new seeds. I stopped after this first hypothesis because it explains every visible cell change and directly distinguishes first-gray stopping from border-only or last-gray alternatives.
