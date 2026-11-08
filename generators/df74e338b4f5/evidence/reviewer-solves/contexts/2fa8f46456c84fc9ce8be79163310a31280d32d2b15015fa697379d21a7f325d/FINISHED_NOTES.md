# Solve work log

## Prior exposure and solve boundary

I had already read the assigned generator and canonical rule during the repair, so earlier rule exposure is **yes**. After this final `prepare` I did not reopen the generator, Racket source, canonical ledger, reference answers, private labels, or the archived earlier solve. This is a human work log based on the newly displayed examples.

## Revision 1

The color-9 cells form separate hollow rectangular frames, nested but often offset from the canvas. Every cell of the other nonzero color is a marker. Outputs preserve all 0 and 9 cells and replace each marker by the number of rectangular frame interiors that strictly contain its coordinate:

- outside all frames → 0;
- inside one frame → 1;
- inside two → 2;
- inside three → 3.

The examples make absolute canvas distance an inadequate rule. In train example 0, markers to the right of the outer frame disappear to 0 while a marker in the outer annulus becomes 1. Train examples 1 and 3 likewise place outside markers near offset frames. The original marker color varies and therefore is not itself meaningful.

I implemented four-connected extraction of each color-9 component, took its bounding box, and counted strict row-and-column containment for every nonzero/non-9 marker. This keeps frame borders unchanged and preserves shape.

Remaining limitation: the visible examples consistently use complete, separated rectangular 9-components. I did not add behavior for malformed or touching frame shapes because the examples do not justify it.
