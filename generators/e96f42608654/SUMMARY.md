# e96f42608654

0-bg grid; cell (0,0) holds a FRAME color; elsewhere a single patterned motif block (random H x W bbox spanning all four sides, with internal zeros, in 2-4 colors). Rule: crop the bbox of all nonzero cells except (0,0) and wrap it in a 1-cell frame of (0,0)'s color. Output dims = (H+2) x (W+2); motif bbox, colors, position and grid size all vary.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
