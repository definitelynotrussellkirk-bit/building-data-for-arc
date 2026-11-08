# Solve notes

This is a human-readable work log based only on the visible examples in `challenge.json`. I had already inspected the assigned family earlier in the generator-review phase, so this is not a blind rule-discovery record; I did not consult generator source, Racket source, private labels, or prior solution notes during this solve phase.

## Hypothesis

Each input is a uniform square with one interior non-background dot. Preserve the dot and draw color 1 vertically through its column, skipping the dot. The horizontal boundary arms depend on whether the dot is on the main diagonal:

- if `dot_row == dot_col`, extend the top endpoint to the right boundary and the bottom endpoint to the left boundary;
- otherwise extend the top endpoint to the left boundary and the bottom endpoint to the right boundary.

Examples 0 and 2 supply the main-diagonal branch. Examples 1 and 3 supply the off-main-diagonal branch. This distinction explains every changed cell and keeps all other background cells unchanged.

## Implementation choices

- Use the top-left cell as the uniform background.
- Scan for the unique non-background dot.
- Copy the grid before painting.
- Paint only background cells on the two boundary arms so the dot would remain intact even in an unusual boundary case.
