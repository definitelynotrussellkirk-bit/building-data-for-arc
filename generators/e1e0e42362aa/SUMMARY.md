# e1e0e42362aa

Remove inert palette/texture/density/position controls; implement exact grid dimensions and cell counts with a literal-grid self_check and rule pin. Adapt unpinned sizes to count endpoints; explicitly reject impossible capacity products. Both duplicate audits are covered.

Default sizes vary by band. Exact dimensions5..15 and cell count1..30 remain available; grid_h*grid_w must exceed n_cells.

See [current notes](notes.md) and [source-bound owner checks](evidence/owner-audit-repair.json).
