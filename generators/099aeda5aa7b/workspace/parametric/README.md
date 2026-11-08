# 099aeda5aa7b native parametric family

The fixed episode parameter is the reflection axis. `horizontal` is the
byte-exact canonical program; `vertical` overlays the top-bottom reflection.
In both settings, stage A computes an input-dependent reflected grid and stage B
overlays its nonzero cells on the original, so reflected conflicts overwrite.

Sampling is independent of the hidden axis. Lessons contain horizontal and
vertical conflicts, asymmetric shapes, axis marks, and symmetric near-misses.
A fixed top-left witness plus guaranteed bottom/right canvas margin exposes the
full-canvas reflection axis and refutes reflection inside only the occupied
bounding box. The fourth query is a populated 30x30 stress case.
