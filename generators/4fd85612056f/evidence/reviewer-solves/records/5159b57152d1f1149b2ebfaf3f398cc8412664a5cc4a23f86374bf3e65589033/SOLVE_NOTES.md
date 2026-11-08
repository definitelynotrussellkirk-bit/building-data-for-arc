# Solve notes

This is the required **post-repair exposed solve**. I had already read and edited
this task's generator before preparation, so `earlier-exposure=yes`; this is not
claimed as an independent blind inference. I did not consult the Racket source,
private labels, reference solutions, or generator code after preparation.

Visible hypothesis: treat every touching nonzero cell as part of the same
4-connected object even when colors differ. Compute each object's bounding-box
height, select the tallest object, and return its tight crop while preserving
colors and zero holes. All four demonstrations have object heights 2, 1, and 3,
and the output is exactly the height-3 object. I used deterministic secondary
keys (cell count, then leftmost column) only to make the program total; the
visible examples do not identify tie behavior.

The two visible queries also have a unique height-3 object, so no tie assumption
is needed for their outputs.
