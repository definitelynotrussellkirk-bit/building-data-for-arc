# Working notes: 751baf3d18b2

- Bounded robustness finding: `self_check(..., meta={"overrides": ...})` validated structure but ignored declared override drift.
- Version 3.0.1 now compares declared axis values with `_analyze` features and emits a precise mismatch diagnostic; matching metadata remains valid. The canonical rule hash remains `56d0892cc35d`.
- The retained test was migrated to `reviewer_support.find_root` / `canonical_path` so it runs in the packet's staged runtime without changing task semantics.
- Regression result: 10 tests and 6 subtests passed. No remaining source-bound failure was found in this bounded check.
