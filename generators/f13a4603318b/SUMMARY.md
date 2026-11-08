# f13a4603318b

0-bg grid with: (a) one DIRECTION marker (color 1/2/3/4) at a corner — 1=up, 2=down, 3=left, 4=right; (b) one connected OBJECT in a non-{0,1,2,3,4,8} color (3-6 cells); (c) a color-8 WALL LINE perpendicular to the sweep, placed so the object hits it after >=2 steps. Rule: translate the object in the marked direction until the next step would hit a wall or the boundary; output = union of all swept positions + the walls, marker removed. (Was: a single 8-cell wall.)

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
