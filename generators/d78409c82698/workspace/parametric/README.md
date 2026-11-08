# d78409c82698 native parametric family

The episode setting is `connectivity ∈ {4, 8}`.  Every input is legal under
both settings and contains the semantic witnesses needed to infer the hidden
choice: red cells isolated under both rules, diagonal-only red groups, cardinal
red components, and non-red distractors.  The default program is byte-for-byte
the canonical 4-neighbor program; the alternative uses all eight neighbors.

`prototype.py` owns sampling, execution, and teaching certificates.
`adapter.py` is the promotion entrypoint described by `promotion.json`.
