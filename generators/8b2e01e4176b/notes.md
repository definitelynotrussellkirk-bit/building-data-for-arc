# Working notes: 8b2e01e4176b

- Bounded robustness finding: an unknown `difficulty` string silently followed the medium defaults.
- Version 3.0.1 now rejects every value outside `None`, `easy`, `medium`, and `hard` with `ValueError`; the canonical rule hash remains `1e68480e5183`.
- Regression result: 9 focused tests passed. No remaining source-bound failure was found in this bounded check.
