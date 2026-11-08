# Working notes: c96915f33c65

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current audit resolution

Allow repeated seed colors independently of positions, force a repeated-color witness every other sample, and declare/test the globally_unique_color_only rival. Both duplicate audits cover the same repaired finding.

Finite repeated-color lesson guarantee; legacy controls outside this audit were not broadly recertified.

Owner-run canonical Racket comparisons and exact tested hashes are in [owner-audit-repair.json](evidence/owner-audit-repair.json); focused regressions are in `tests/`. The receipt retains each covered return ID and old audited source. Approval was not refreshed by these edits.
