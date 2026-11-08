# Post-repair visible-only solve notes

## Exposure declaration

I had already inspected and repaired this task's generator before this episode, so this is **not blind**. During this solve episode I did not reopen the generator, Racket rule, private labels, reference solutions, or earlier solution explanations. I used only the displayed visible examples and my own implementation.

## Hypothesis

Each nonzero color marks two endpoints. Fill the inclusive segment only when the two cells lie on a 45-degree diagonal (`abs(dr) == abs(dc)` with nonzero row displacement) and every interior cell is background. Horizontal, vertical, and other non-diagonal pairs remain unchanged.

Visible discriminators:

- Train 1 leaves color 9 horizontal while filling diagonal colors 6 and 4.
- Train 2 leaves color 1 vertical while filling diagonal colors 8 and 9.
- Train 0 fills all three clear diagonal pairs.

The implementation groups positions by color, tests every same-color pair against the original input, and paints qualifying paths into a copy. Testing against the original prevents one newly painted segment from creating or blocking a later rule trigger.
