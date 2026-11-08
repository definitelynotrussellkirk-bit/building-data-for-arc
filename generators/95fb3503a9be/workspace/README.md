# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

## Canonical relation-support census

`relation_support_census.py` compares the frozen review baseline with the current generator over complete four-sample lessons. It measures two canonical relational features that the ordinary pooled gates did not expose in the inherited 3.0.0 source:

- overlap between component bounding-box column ranges;
- support for a crop at least four columns wide.

It also executes the two corresponding shortcuts, `column_bands` and `crop_width_three`, and fails unless every sampled four-example lesson contains a counterexample to both.

From the packet repository:

```bash
PYTHONPATH=src python3 generators/95fb3503a9be/workspace/relation_support_census.py \
  --seeds 500 --out ../checks/relation-support-census.json
```

The output path is exclusive: choose a new filename for a repeat run. Use `--report-only` to retain a failing exploratory census without a nonzero exit.
