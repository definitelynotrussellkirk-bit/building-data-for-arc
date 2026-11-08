# Solve work log

## Prior exposure

I had already inspected this task's generator and canonical rule while repairing it, so this is **not blind**. During this solve episode I kept those files closed and used only the newly prepared visible examples. I did not consult a reference solution or private labels.

## Revision 1 — reflected beam

The red cell (2) is the emitter and the adjacent blue cell (1) specifies the initial cardinal direction from red toward blue. Starting one cell beyond blue, traverse one cell at a time. Paint only background cells (0) cyan (8), retain all nonzero cells, and stop before a gray wall (5) or the grid edge.

The visible paths distinguish the mirror mappings:

- color 3 behaves as `/`: `(dr, dc) -> (-dc, -dr)`;
- color 4 behaves as `\\`: `(dr, dc) -> (dc, dr)`.

Train 0 confirms an upward launch, a color-3 right turn, then a color-4 downward turn. Trains 1 and 2 confirm repeated reflections and that walls terminate without being recolored. I implemented a 500-step cap to make malformed loops bounded. Remaining uncertainty is only whether an unseen malformed input might have missing/nonadjacent markers; the solver conservatively returns it unchanged.
