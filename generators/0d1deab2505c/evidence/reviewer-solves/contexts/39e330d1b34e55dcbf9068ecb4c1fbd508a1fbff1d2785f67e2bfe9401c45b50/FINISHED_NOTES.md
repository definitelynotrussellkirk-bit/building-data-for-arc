# Solve notes — visible examples only

This is a human work log. I had earlier rule exposure from reviewing the assigned generator, so this is not a blind solve; during this solve phase I used only the prepared visible examples and did not consult generator, Racket, reference-solution, or private-answer files.

## Revision 1 hypothesis

Each color-4 cell is the center of a five-cell cross. Exactly one color-1 component begins two cells away in a cardinal direction and acts as that creature's tail. Treat the cross and its entire 8-connected blue tail as one object.

The object translates toward the wall opposite the tail until the bounding box of body plus tail touches that wall. The blue tail keeps its shape and orientation while moving. The cross body turns 180 degrees around its translated center, so top/bottom arm colors and left/right arm colors swap. Erase every source object before painting any destination object so multiple creatures are handled independently.

The three visible demonstrations support the same rule for vertical and horizontal motion, one through four creatures, straight/forked/asymmetric tails, and varied arm colors. I implemented this directly with cross detection, an 8-connected tail flood fill, bounding-box displacement, and opposite-arm repainting.
