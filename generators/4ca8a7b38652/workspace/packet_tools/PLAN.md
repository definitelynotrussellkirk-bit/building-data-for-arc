# ARCpuzzles packet ZIP tooling implementation plan

**Goal:** Inspect and selectively materialize the issued packet without a full extraction, while preserving all selected bytes and reporting the exact verification scope.

**Architecture:** One standalone Python standard-library CLI and one synthetic integration test module. The CLI reads the original canonical manifest, rejects unsafe or ambiguous archive headers, and treats every member selection as a partial scope unless it equals the entire original inventory. It never imports or runs packet code, draws assignments, edits manifests, or packages returns.

**Files:** `packet_zip.py` implements `inspect`, `plan`, `materialize`, and `verify`; `test_packet_zip.py` exercises real temporary ZIPs; `README.md` documents commands, scope, and the official startup/packaging limitations.

**Constraints:** Work only in this tooling directory. Do not extract the actual source archive here. Read no generator, rule, notes, or evidence contents. Preserve the original manifest bytes and all selected file bytes. Use no dependencies or network access.

## Implementation

- [x] Write and run failing CLI integration tests for exact partial extraction, selected/all verification, corruption, missing requests, path traversal, symlinks, duplicates, preexisting destinations, and resource budgets.
- [x] Implement conservative path/header and canonical manifest validation; make all selector misses explicit errors.
- [x] Implement streaming SHA-256 checks and new-destination materialization, with a partial-scope receipt written before extraction and completed only after every selected member passes.
- [x] Run the complete synthetic suite. The real metadata-only attempt was killed under shared-memory pressure; no successful real packet plan is claimed.
- [x] Document deterministic selectors, exit codes, receipt interpretation, existing official runtime closure reuse, and sparse packaging limitations.

## Review focus

Hostile filenames must fail before creating a destination. Corrupt selected files must never be reported as verified. A matching partial checkout must never imply that missing original files were checked. No existing output may be overwritten. Resource limits include the automatically preserved manifest and entry files.

## Authorized optional extension

A separate local copied-builder proposal adds --source-zip to support fully verified immutable originals from the source ZIP. It preserves the default physical-inventory path and the stock patch, INTAKE, and return-validation machinery. The exact original, diff, origin hashes, synthetic regressions, and independent official-validator command result are retained. This proposal remains pending shared integration. No real source ZIP verification or real review packaging was executed by the tooling agent.
