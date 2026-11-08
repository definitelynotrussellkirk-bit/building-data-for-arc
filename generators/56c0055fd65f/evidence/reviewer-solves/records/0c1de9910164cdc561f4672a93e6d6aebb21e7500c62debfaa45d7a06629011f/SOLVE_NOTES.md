# Solve work log

## Exposure declaration

Before this solve episode I had already reviewed task `56c0055fd65f`'s generator,
canonical examples, and rule binding as part of the assigned repair, so this is
an exposed post-repair solve. After `solve_episode.py prepare` I did not reopen
the generator, Racket source, canonical private labels, prior solution text, or
query answers. I used only the visible challenge presentation and my own Python.

## Revision 1 — topology / enclosed-hole hypothesis

Across all three visible demonstrations, every 4-connected yellow component is
recolored uniformly while zeros and the color-6 domino are preserved. The output
color depends on the number of enclosed zero regions inside the component:

- no enclosed zero region -> red `2`;
- one enclosed zero region -> green `3`;
- two enclosed zero regions -> cyan `8`.

The examples rule out simple area or position lookup: in train example 1 the two
10-cell components receive different colors, and train example 2 moves the
roles to different positions. I implemented 4-connected yellow-component
extraction, then counted 4-connected zero regions inside each component's
bounding box, excluding regions that touch that box's edge. The solver copies
the input and recolors only yellow component cells, preserving color 6 and all
background cells.

Remaining uncertainty before checking: the visible examples only show 0, 1, and
2 holes, so the fallback leaves a component yellow if an unseen count occurs.
The two visible queries appear to stay inside the demonstrated range.
