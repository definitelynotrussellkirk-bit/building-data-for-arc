# Signed anchor-vector family for `8dafcfb1101f`

The private episode setting is `vector_direction=src_to_dst|dst_to_src`. The
canonical default is byte-for-byte the selected source rule. Both variants first
read the two marker locations, produce a signed displacement vector, then use
that input-dependent intermediate to translate every payload cell on a fresh
empty grid.

Inputs are sampled independently of the setting and remain lawful in both
directions. The three-demo minimum covers positive and negative row/column
components and rejects identity, absolute-vector, one-axis, swapped-axis,
fixed-offset, and marker-moving shortcuts. Every episode has four distinct
queries; the last is a substantive 30x30 boundary case.

Focused check:

```bash
PYTHONPATH=src:shared/runtime:. pytest -q \
  generators/8dafcfb1101f/tests/test_parametric_translation.py
```

Native authoring qualification is run by the packet wrapper with three demos and
four queries. This prototype is not accepted or training-admitted by itself.
