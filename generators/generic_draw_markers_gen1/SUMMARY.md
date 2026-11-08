# generic_draw_markers_gen1

gen1: recolor base noise (A->B), then draw a FULL CROSS (row+col) in a NEW
color centered on every marker cell -- markers (a distinct color) drive WHERE
each cross is drawn; the cross color is absent from the input.

Transform: (pipe (recolor g A B) -> for each marker (r,c): (draw-cross g r c NEW)).
Composes a color recolor with the draw-from-markers cross step.

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
