# Working notes: 40c64eba6ac8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current audit resolution

Remove inert palette/position/density aliases and singleton pseudo-axes. Exact shape_h/shape_w accept2..6 in every band, unknown controls reject, and connected full-bbox fallback masks preserve all four nonempty Boolean regions.

Private negative textures remain diagnostic fixtures outside the ordinary override contract.

Owner-run canonical Racket comparisons and exact tested hashes are in [owner-audit-repair.json](evidence/owner-audit-repair.json); focused regressions are in `tests/`. The receipt retains each covered return ID and old audited source. Approval was not refreshed by these edits.

Difficulty bands implement a proposed size progression. The checks establish observable size support, not calibrated solver or learning difficulty.
