# Review workspace

The selected implementation is `../generator.py`; workspace files are never automatically selected.

`reference_probe.py` is an independent review oracle for this task. It can be imported by portable task tests to:

- compute the additive main-diagonal reflection without calling production helpers;
- compute the canonical-fitting `upper_triangle_only` rival;
- observe the three exact controls;
- diagnose teaching-contract and malformed-grid failures; and
- load a source-selected generator through `GENERATOR_UNDER_TEST`.

The selected regression suite is `../tests/test_generator.py`. It resolves the packet/repository with `reviewer_support.find_root` and canonical data with `reviewer_support.canonical_pairs`, so it runs in both the source tree and the portable task-test snapshot.
