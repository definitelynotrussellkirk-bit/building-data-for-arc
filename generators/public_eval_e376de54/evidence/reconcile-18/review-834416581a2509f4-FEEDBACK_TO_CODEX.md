**F1: Add first-party public-authoring export and witness commands.**

The public preflight schema contains everything needed for sequential one-query export and source-bound causal replay, but the bundled native tools target qualification receipts. The reusable `checks/tools/export_preflight_queries.py` and `checks/tools/build_source_bound_witness.py` demonstrate the missing workflow, including hidden-field byte invariance and protected replay.

**F2: Add a compact mode to `review_public_task_tests`.**

Each successful task-test run retained a roughly 7 MB frozen runtime copy even though `result.json`, `source-binding.json`, the log, and JUnit XML contain the useful reviewer evidence. A supported `--compact` mode that removes the temporary runtime after hashing would make return preparation safer and smaller.

**F3: Document pytest isolated import mode for multi-home focused runs.**

Different generator homes conventionally use identical filenames such as `test_native_family.py`. Collecting two homes together under pytest's default import mode causes a module-name collision. The frozen per-task harness already uses `--import-mode=importlib`; the packet guidance should recommend the same option for combined focused suites.

**F4: Let preflight accept an existing empty output directory.**

`review_public_creation preflight` fails when its output directory already exists, even if empty. Accepting an empty directory—or emitting a more explicit diagnostic—would reduce fragile cleanup logic in scripted reviewer runs while preserving fail-closed behavior for nonempty evidence directories.
