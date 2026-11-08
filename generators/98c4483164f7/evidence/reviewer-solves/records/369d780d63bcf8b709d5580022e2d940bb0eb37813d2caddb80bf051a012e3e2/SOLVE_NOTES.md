# Solve work log

## Prior exposure

Before this solve episode I had already inspected and repaired this task's Python generator and had seen the canonical task rule while synchronizing its authority copy. I therefore record **earlier rule exposure: yes**. During this solve episode I did not reopen the generator, Racket program, reference solutions, private labels, or earlier solution explanations; I used only `solve/challenge.json` and visible-example execution.

## Revision 0 — skeleton

The provided `solve/solution.py` raised `NotImplementedError`. A direct import-and-call probe confirmed that expected failure before implementation.

## Revision 1 — diagonal rays selected by marker corners

Visible pattern:

- Every input has one filled 2×2 nonzero motif.
- Color `2` marks one or more corners; the other nonzero color is the output paint.
- The entire motif becomes the paint color.
- A marker at top-left, top-right, bottom-left, or bottom-right activates the corresponding outward NW, NE, SW, or SE diagonal direction.
- Every one of the four motif cells emits a ray in each active direction. Their overlap produces the three-cell-wide diagonal bands visible in the examples.

The implementation finds the nonzero 2×2 bounding box, derives active directions from its color-2 cells, recolors the motif, and extends each selected diagonal to the boundary. It validates malformed/non-rectangular motifs rather than silently guessing. The remaining uncertainty is only private-query correctness; all visible examples should be exact under this rule.
