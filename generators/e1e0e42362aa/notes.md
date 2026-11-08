# Working notes: e1e0e42362aa

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current audit resolution

Remove inert palette/texture/density/position controls; implement exact grid dimensions and cell counts with a literal-grid self_check and rule pin. Adapt unpinned sizes to count endpoints; explicitly reject impossible capacity products. Both duplicate audits are covered.

Default sizes vary by band. Exact dimensions5..15 and cell count1..30 remain available; grid_h*grid_w must exceed n_cells.

Owner-run canonical Racket comparisons and exact tested hashes are in [owner-audit-repair.json](evidence/owner-audit-repair.json); focused regressions are in `tests/`. The receipt retains each covered return ID and old audited source. Approval was not refreshed by these edits.

Difficulty bands implement a proposed size progression. The checks establish observable size support, not calibrated solver or learning difficulty.
