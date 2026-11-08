# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before preparation I had read and repaired this task's generator and had inspected the canonical rule/output authority, so earlier rule exposure is **yes**. During this solve I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Visible-example hypothesis

All color-1 cells form disconnected rectangular outlines and remain color 1. For each zero cell, count how many outline bounding boxes strictly contain its coordinate. A zero outside every rectangle remains 0; a zero inside one, two, or three rectangles becomes 2, 3, or 4 respectively. The rule uses actual containment, not distance from the outer border or an assumption that all frames share a center.

Evidence from the visible examples:

- Train 1 has two nested frames and fills the outer band with 2 and the inner interior with 3.
- Trains 0 and 2 have three frames and introduce color 4 only strictly inside the innermost frame.
- Existing color-1 outlines are unchanged, and zeros outside the outermost frame remain 0.
- The query layouts include displaced/asymmetric nesting, so I extract each 4-connected color-1 component's bounding rectangle independently and test strict containment per cell.

## Revision 1

Implemented component extraction for every color-1 outline, converted each component to its bounding box, and painted zero cells by nesting depth. This directly represents the visible relation and avoids row/column hard-coding. I expect it to cover both query grids without relying on concentricity.

Remaining uncertainty before checking: the visible examples strongly support complete rectangular components, but the code deliberately does not validate outline completeness because the solve only needs to transform the supplied lawful instances.
