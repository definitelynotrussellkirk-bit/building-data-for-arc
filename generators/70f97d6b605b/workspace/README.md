# Selector contract replay

Run from the extracted packet root after installing its offline Racket bundle and Python dependencies:

```bash
python3 run_with_racket.py python3 generators/70f97d6b605b/workspace/replay_selector_contract.py --out ../checks/selector-replay --seed 0 --samples-per-band 35
```

Use a new output directory. The standard-library verifier loads portable canonical pairs, the sibling `counterexamples/selector_cases.json`, and 35 default inputs per band. It labels inputs only through the supported public `arcpuzzles apply` command, batching at most 64 grids. It records source/fixture/verifier hashes, raw subprocess logs, commands, original authority receipts, visible controls, canonical shortcut fits, witness firings, every linked-rival refutation, and generated coverage for each lesson competitor. Missing declarations, vacuous witness coverage, malformed results, source drift and subprocess errors fail explicitly.

This checks case-level semantic claims. Use the shared `lesson-census` for production sampling and query rotations; the replay tool does not replace the lesson census or grant approval.

The final return `review-559c80d6820285f7` retains a passing 122-case run in `checks/selector-contract-complete/`, failed earlier iterations, focused tests, and both censuses. Large native reports are losslessly compressed; after extracting the evidence bundle, run `python3 checks/restore_evidence.py` to restore their original paths with byte/hash verification.
