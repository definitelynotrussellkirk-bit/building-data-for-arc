# Solve work log

## Prior exposure

Before this solve episode I had already inspected the selected task authority while repairing the generator, so this is **not blind**. During this solve I did not reopen or consult the Racket rule, generator implementation, reference solutions, private query labels, or prior solution explanations. I used only the visible examples in `solve/README.md` / `challenge.json` and my own calculations.

## Hypothesis from the visible examples

Every input has height `n`, width `3n+2`, and two full color-5 columns separating three `n x n` panels. The first two panels demonstrate a geometric transform; the output is the third panel under that same transform.

Visible checks:

- Example 0: the first-panel L shape maps to the second panel by a 90-degree clockwise rotation. Applying that rotation to the color-9 third panel reproduces the shown output.
- Example 1: the first panel maps to the second by a 180-degree rotation. The same rotation reproduces the color-1 output.
- Example 2: a quarter-turn maps the color-9 demonstration panels, and applying it to the color-2 query panel reproduces the shown 6x6 output.

I therefore implemented all square dihedral transforms plus identity, selected the unique transform mapping panel A exactly onto panel B without cropping or recentering, and applied it to panel C.

## Manual query predictions used as a sanity check

- Query 0: A->B is a left-right reflection. The color-3 output should contain cells `(3,2),(3,3),(4,3),(5,2),(5,3),(6,2)` in a 7x7 grid.
- Query 1: A->B is a clockwise quarter-turn. The color-9 output should contain `(0,0),(0,1),(0,2),(1,2)` in a 4x4 grid.

## Alternatives rejected

- Normalizing each colored shape before comparing it would discard absolute panel placement; the examples preserve the full square frame.
- Copying panel C unchanged fails example 0.
- Applying the reverse B->A transform is distinguishable on the quarter-turn examples and fails their outputs.

## Remaining uncertainty

The examples show a unique square transform per item. The solver fails loudly if a future item is ambiguous rather than silently choosing an arbitrary transform.
