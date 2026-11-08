# Workspace

The selected implementation is `../generator.py`; workspace files are review tools or source-bound receipts and are never selected automatically.

- `review_probe.py` is a portable, source-bound regression probe. It checks all ten labelled canonical pairs, all five canonical profiles, representative full override combinations in every band, canonical-shortcut truthfulness, and all rotations of representative three-demo/one-query lessons. Run it through the packet runtime: `python3 review.py run python3 generators/83ca9df09514/workspace/review_probe.py`.
- `manual_authority_sync.py` creates and applies a narrow JSON-pointer patch only after checking the expected source hashes, expected old values, canonical target bytes, and archival `raw_code` preservation.
- `manual_authority_sync_plan.json`, `.diff`, and `_receipt.json` retain the proposed and applied authority synchronization with exact hashes and execution-parity evidence.

The retained semantic counterexample is in `../counterexamples/semantic_shortcuts.json`; focused tests replay it against the final generator hash.
