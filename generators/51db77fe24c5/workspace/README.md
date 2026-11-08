# Reviewer workspace for 51db77fe24c5

`reference_probe.py` is a source-independent companion for future reviews. It
contains:

- a transparent four-connected-component oracle;
- the historical three-mask memorizer;
- bounding-box, size-four, all-blue, and identity rivals;
- component-mask classification and exact-axis observation;
- a fixture that demonstrates why the historical finite-mask grammar was unsafe.

Typical focused run from the packet root:

```sh
PYTHONPATH=repo/shared/runtime \
python3 -m pytest -q repo/generators/51db77fe24c5/tests/test_generator.py
```

Authoritative integration checks still use the shared Racket-backed commands in
`DUTIES.md`; this probe is supplemental and intentionally does not import private
runner functions.
