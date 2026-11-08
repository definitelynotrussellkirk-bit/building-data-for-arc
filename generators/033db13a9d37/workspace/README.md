# Workspace

`reference_probe.py` is the retained independent authoring probe for task `033db13a9d37`. It deliberately computes the first-nonzero oracle and last-nonzero rival without importing production rule helpers, reads canonical pairs through `reviewer_support`, observes exact axes, and exhausts requested four-pair schedule starts under all four query rotations.

Example from a prepared portable runtime:

```sh
python3 generators/033db13a9d37/workspace/reference_probe.py \
  --starts 64 --out ../checks/curriculum-starts.json
```

The selected implementation remains `../generator.py`; workspace drafts are never automatically selected. The probe exposes canonical answers and must not be used during visible-only solve episodes.
