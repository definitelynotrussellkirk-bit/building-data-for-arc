# a26a4c54123f

A grid of rooms (R x C, total >=2) built by rectangular_rooms with COLOR-1 (blue) walls and uniform room interiors (size 3..6). The SEEDED room holds one COLOR-2 (red) cell at a random interior cell and has EXACTLY ONE COLOR-7 (orange) DOOR to a neighbour (the target). 0-2 extra distractor doors connect OTHER room pairs (never the seed room). Rule (DOOR-DIRECTED FILL): find the seeded room, follow its single door to the adjacent room, and output walls+doors with that target room filled COLOR 8 (everything else 0). The layout, room size, seeded room, door direction and distractor doors all vary freely (was a fixed 1x2 layout x 3 sizes).

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
