# generic_draw_markers_gen2

gen2: recolor markers (marker_color -> NEW), then SMEAR that NEW color in a
fixed direction -- from each marker a ray of the NEW color shoots until it hits
a wall or a base-noise obstacle. Markers (a distinct color) drive WHERE rays
originate; NEW is absent from the input. Composes recolor + ray/smear.

Transform: (smear-color (recolor g marker NEW) NEW dir).

Kind: `generic`. Imported version: `1.3.0`.
Approval is derived by the catalog from current code and retained evidence.
