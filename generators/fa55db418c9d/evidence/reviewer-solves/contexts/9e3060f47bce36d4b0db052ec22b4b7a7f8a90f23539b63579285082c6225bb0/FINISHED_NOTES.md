# Solve work log

## Exposure declaration

Before this fresh episode I had already inspected the assigned generator and canonical task while repairing it, so this is **not a blind solve**. During the solve phase itself I used only `solve/challenge.json`, my own Python implementation, and visible-only check feedback. I did not reopen the generator, Racket source, reference solutions, private labels, or prior solution explanations.

## Visible-example observations

Across the five demonstrations, nonzero cells separate naturally into same-color cardinal components. Non-blue components remain unchanged. Blue components also remain unchanged when they are squares, straight runs, rectangles, or other non-L shapes.

Every changed object is a blue three-cell component occupying three corners of a `2×2` box. The replacement color is constant across the component and depends on the missing corner:

- missing southeast → `2`
- missing southwest → `3`
- missing northeast → `4`
- missing northwest → `8`

The examples include all four orientations, non-blue L shapes that stay unchanged, blue non-L components that stay unchanged, and edge cases. That distinguishes the exact component/shape/color rule from recoloring all size-three blue objects or all L shapes.

## Revision 1

Implemented a pure Python `solve(grid)` that:

1. copies the grid;
2. finds exact-color four-connected components;
3. selects only color-1 components with exactly three cells and a `2×2` bounding box;
4. finds the single missing normalized corner; and
5. recolors the selected component using the mapping above.

All other cells are left untouched. The implementation handles border components without padding assumptions and does not mutate the input.

## Remaining uncertainty

The visible examples strongly determine the rule. The main residual uncertainty is only whether the hidden queries contain unusual lawful contacts; exact-color component extraction should handle those consistently.
