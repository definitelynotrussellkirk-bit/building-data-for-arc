# Workspace

`reference_probe.py` is an independent geometry oracle and distribution probe for task `017f1406edaf`. It intentionally does not import production helpers from `generator.py` other than through its explicit dynamic-loader entry point.

It provides:

- monochrome 4-connected component extraction;
- an independent intended-rule mirror;
- the three retained rivals (`count_all_blue`, `include_row0_size_match`, and `median_candidate_size`);
- observable-axis recovery; and
- a JSON sample report for future reviews.

Example from `repo/`:

```sh
PYTHONPATH=shared/runtime python3 generators/017f1406edaf/workspace/reference_probe.py --per-band 200
```

The selected implementation is `../generator.py`; workspace tools are diagnostic and are never automatically selected.
