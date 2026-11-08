# generic_draw_markers_gen3

gen3: recolor base noise (A->B), then CONNECT each aligned marker pair with a
straight LINE in a NEW color. Markers come in pairs sharing a row (or a column);
each pair's two cells are joined by a segment of the NEW color, which is absent
from the input. Composes a recolor with the draw-line-between-markers step.

Transform: recolor A->B, then for each marker line/col draw-line between its two
markers in NEW.

Kind: `generic`. Imported version: `1.2.0`.
Approval is derived by the catalog from current code and retained evidence.
