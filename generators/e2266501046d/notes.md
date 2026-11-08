# Working notes: e2266501046d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current audit resolution

Reject Boolean/float/string colors and negative or noninteger sample indices; compare exact metadata by type and value. Migrate direct tests to portable reviewer_support helpers. Both duplicate audits are covered.

Legacy shared draw helpers keep their old behavior; this generator opts into strict draws.

Owner-run canonical Racket comparisons and exact tested hashes are in [owner-audit-repair.json](evidence/owner-audit-repair.json); focused regressions are in `tests/`. The receipt retains each covered return ID and old audited source. Approval was not refreshed by these edits.
