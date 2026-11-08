# Review workspace for 506e262f9354

The selected implementation is `../generator.py`.

`reference_probe.py` intentionally does not import production geometry.  It
loads canonical pairs, computes the selected transformation independently,
and exposes the two strongest canonical-fitting rivals:

1. `line_length_rival` — limits triangle height to the source-line length;
2. `preserve_decoys_rival` — retains nonzero cells outside the triangle.

Useful replay:

```bash
python3 -m pytest ../tests/test_generator.py -q
```

Retained machine-readable witnesses are under
`../counterexamples/review-03a14c3c057deb90-v0001/`.
