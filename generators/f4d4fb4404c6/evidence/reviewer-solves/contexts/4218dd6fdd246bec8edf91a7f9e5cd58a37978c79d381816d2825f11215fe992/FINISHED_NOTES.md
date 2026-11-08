# Final visible-only solve notes

## Exposure declaration

This is an exposed post-repair solve. I had already reviewed the task and therefore declare earlier rule exposure. During this final episode I opened only `solve/challenge.json`; I did not reopen the generator, Racket source, canonical records, hidden labels, or the preserved earlier solve.

## Visible hypothesis

The demonstrations contain hollow 4×4 frames and blue (`1`) border strips. A border strip selects the frame whose perpendicular span overlaps it, even when the strip covers only part of that span. The output removes all blue markers, keeps each frame in its own color, and repeats that frame every four cells toward every selected border, clipping a final ring at the boundary. Distinct markers and distinct frame colors act independently.

## Revision 1

Implemented a clean parser for hollow frames and connected border markers, followed by clipped four-cell-step replication. No deliberate wrong example or hidden-answer consultation was used.
