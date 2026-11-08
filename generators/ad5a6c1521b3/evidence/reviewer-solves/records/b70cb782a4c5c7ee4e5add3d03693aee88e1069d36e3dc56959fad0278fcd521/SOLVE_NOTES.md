# Post-repair visible-only solve log

## Isolation and prior exposure

I had already inspected this task's generator/rule material while repairing it, so this episode must be recorded with `earlier-exposure=yes`. After `solve_episode.py prepare`, I kept the generator, Racket rule, reference solutions, private labels, and earlier solution explanations closed. The implementation below was reconstructed from the three visible input/output pairs only; no reference was consulted during the solve.

## Visible observations

- The most frequent color behaves as background (5, 1, and 0 in the three demonstrations), so background is not fixed to zero.
- Foreground cells split into 4-connected monochrome components.
- A color with only one component is left unchanged (color 8 in examples 0 and 2).
- When a color has multiple components, only one survives. The demonstrations select the component with greatest area.
- The equal-size color-4 components in example 1 resolve in favor of the lower/right component. I encode “lower/right” as the greatest top-left `row + column`; the visible data contains one tie witness, so this is the narrowest translation-invariant tie rule supported by it.
- All old components of a selected color are erased. The winner is replaced by a solid rectangle covering its bounding box and extending one column to the left. This both fills holes and explains the extra output column.
- Each foreground color is treated independently: example 1 transforms both colors 4 and 6, while example 2 transforms color 3 and preserves the single color-8 component.

## Predicted queries

For query 0 (background 0):

- Color 1 has two area-4 components, so the lower/right one wins. Its rows 3–5 and columns 5–6 become a solid rectangle extended left through column 4.
- Color 5 has components of areas 2 and 5, so the lower-left area-5 component wins. Its rows 3–5 and columns 1–2 become solid and extend left through column 0.

Thus rows 3–5 contain `5 5 5 0 1 1 1 0`, with all other cells background.

For query 1 (background 7):

- The area-6 color-2 component at upper left beats the area-3 lower component. Its rows 1–3 and columns 1–3 become solid and extend left through column 0.
- Color 9 has one component and remains unchanged.

## Program design

The solver finds the modal background, enumerates 4-connected components from the immutable input, selects by `(area, top-left row + top-left column)`, clears repeated colors, and paints the extended solid winner rectangle. Passive single-component colors are preserved. Remaining uncertainty is limited to unseen exotic ties whose components are not cleanly ordered lower/right; the supplied tie demonstration and both visible queries are decisive for the implemented cases.
