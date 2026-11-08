# Solve work log

## Exposure declaration before solving

I had not opened task `9af68e46cf69`'s generator, Racket rule, reference solution,
private labels, audit evidence, or prior solve notes. I used only the prepared
`challenge.json`/README and my own local checks.

## Visible-example observations

All examples use background 9 and foreground objects of color 1. Output shape is
unchanged. Some complete 4-connected 1-components are recolored to 8, while all
other cells are retained. In every recolored component, the component encloses a
background cavity under 4-connectivity. Examples include a 3x3 ring and larger
irregular loops. Components with a concavity that remains connected to the
exterior, line fragments, and isolated cells stay 1.

## Revision 1 hypothesis and implementation

Hypothesis: recolor each entire 4-connected color-1 object from 1 to 8 exactly
when that object has at least one hole. For each component, I create a one-cell
padded copy of its bounding box, treat only that component as a wall, flood the
complement from the padded boundary, and detect any unreached complement cell.
This avoids mistaking a border-touching object or a nearby separate object for a
closed cavity.

Local probe: run `solve` on every visible training input and compare it with the
visible training output from `challenge.json`. Remaining uncertainty is limited
to whether unseen data changes the foreground/background colors; all visible
examples consistently use 1, 8, and 9, so the implementation follows that rule.
