# Visible-only solve notes

Human work log. I used only `solve/challenge.json` during this episode. I had seen the task rule earlier while reviewing the generator, so this is not a blind solve; the final exposure declaration will say `yes`.

## Hypothesis from the five visible examples

Each input is six equal 4×4 panels separated by full columns of 9. Treat every nonzero cell inside a panel as the object's support and ignore its color.

The first two panels form A:B. After translating both supports to the top-left, B is the first matching transform of A in this order: identity, 90° clockwise, 180°, 270°, then left-right reflection. Apply that same transform to the normalized support in C (panel 3). Among the three candidate panels, select the unique candidate whose normalized support matches the transformed C. Return a 4×4 grid containing that candidate at its original in-panel offset, recolored 8.

The examples rule out choosing candidate 1, using the inverse rotation, and normalizing the chosen candidate's output position: winners occur at later ranks, the clockwise/counterclockwise distinction matters, and the cyan support retains nonzero offsets.
