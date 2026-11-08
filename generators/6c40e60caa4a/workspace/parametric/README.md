# Native seeded-frame scope family

`frame_scope=deepest` is the exact selected canonical rule. The alternate
`frame_scope=all_seeded` fills the interior of every frame containing a red seed.
Both settings first infer seeded frame chains from the input; the resulting frame
set is then consumed by the fill operation. Inputs are setting-independent, use
2–6 demonstrations and 1–4 queries, and include a substantive 30×30 query.

Run focused checks from the repository root:

```bash
PYTHONPATH=shared/runtime:. pytest -q generators/6c40e60caa4a/tests/test_parametric_native.py
```
