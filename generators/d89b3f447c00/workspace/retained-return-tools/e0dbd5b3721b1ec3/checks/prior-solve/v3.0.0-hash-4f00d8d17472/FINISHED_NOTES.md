# Solve work log

## Prior exposure

Before this visible-only solve I had already inspected the task's canonical rule and generator as part of the assigned repair. I therefore mark `earlier-exposure yes`. During this solve I did not reopen either source, consult reference solutions, or inspect private labels; I used only `challenge.json`, the visible examples, and my own code.

## Hypothesis

Every changed cell completes the fourth corner of an axis-aligned rectangle. The other three corners already have the same nonzero color. This is color-local: background stays zero and unrelated markers—including a fourth same-color marker that is not part of the target rectangle—remain unchanged.

Examples supporting it:

- Train 0 completes color 4 at `(0,2)` from `(0,6),(2,2),(2,6)`, and color 9 at `(3,8)`.
- Train 1 demonstrates five colors at once and also has an extra color-3 marker at `(4,9)`; only the missing rectangle corner `(6,10)` is added for that color.
- Train 2 similarly leaves the extra color-6 marker `(3,3)` untouched while adding `(6,4)`.
- Train 3 includes two-cell-wide/two-cell-high minimal rectangles, so the rule is not restricted to large rectangles.

## Implementation choice

I enumerate pairs of occupied rows and columns separately for each nonzero color. If exactly three of the four induced corners have that color in the original input, I paint the fourth in a copied output. Detection uses the original grid rather than newly painted cells, preventing accidental iterative cascades not evidenced by the examples.

## Expected query changes

- Query 0: add color 7 at `(5,8)` and color 9 at `(5,0)`.
- Query 1: add color 6 at `(1,14)`, color 4 at `(3,14)`, color 7 at `(4,3)`, color 5 at `(6,13)`, and color 3 at `(10,16)`.

Remaining uncertainty is limited to hypothetical inputs with overlapping conflicting candidate rectangles; no visible example contains such a conflict. The one-pass interpretation is the smallest rule consistent with all visible pairs.
