# Working notes: afa7a3af9331

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current audit resolution

Replace the unrelated op-key/set-mask sampler with exactly two normalized objects; preserve object colors and paint overlap8 under unchanged Racket authority. Pin the rule and require connected operands.

Only exact shape_h/shape_w controls (2..6); default sizes increase with difficulty.

Owner-run canonical Racket comparisons and exact tested hashes are in [owner-audit-repair.json](evidence/owner-audit-repair.json); focused regressions are in `tests/`. The receipt retains each covered return ID and old audited source. Approval was not refreshed by these edits.

Difficulty bands implement a proposed size progression. The checks establish observable size support, not calibrated solver or learning difficulty.
