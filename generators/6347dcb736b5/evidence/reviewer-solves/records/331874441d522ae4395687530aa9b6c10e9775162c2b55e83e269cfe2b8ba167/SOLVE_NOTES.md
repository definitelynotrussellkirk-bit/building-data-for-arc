# Visible-only solve notes

Earlier rule exposure: **yes** from the assigned generator review. During this solve I read only `solve/challenge.json`; I did not reopen generator code, Racket source, reference solutions, prior solve explanations, or private labels.

## Hypothesis

Treat every nonzero same-color 4-connected component as a separate object. On a fresh zero canvas, replace that object by the perimeter of its axis-aligned bounding box in the same color.

Visible evidence:

- Training example 1 turns each irregular component into its rectangle border; the larger 9-object leaves its bbox interior zero.
- Training example 2 contains two disconnected color-7 components. They are outlined separately rather than merged into one color-wide box, while the color-9 component becomes a filled-looking 2-row outline because its bbox has height 2.
- Training example 3 again treats disconnected color-3 components independently and erases occupied interior cells when they are not on the perimeter.

Implementation: row-major scan, same-color 4-neighbor flood fill, one bbox per component, then paint only each bbox perimeter onto a blank grid.
