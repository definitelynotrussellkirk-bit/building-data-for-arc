# Native rectangle-fill cascade family

`cascade_mode=canonical` returns the exact archival rule.  `triggered_cascade`
keeps that first stage and then bridges every two-point color whose endpoints hit
exactly one cell still painted with the first qualifying rectangle's color.
Overlapping qualifying rectangles make the completed Stage-A grid—not raw bbox
coverage—causally necessary.

The sampler is matched across settings, supports 2–6 demonstrations and 1–4
queries, always builds all six/four profiles before slicing, and ends with a
30×30 query.  Every scene contains two overlapping qualifiers, two positive
triggers, an overwritten-overlap decoy, a two-anchor decoy, close four-cell and
three-cell negatives, and a many-cell nuisance profile spanning the canvas.
Mirrored rectangle layouts and crossed boundary/interior trigger profiles prevent
fixed-corner and fixed-rank shortcuts from identifying the active pairs.

Run the focused tests and probe from the repository root:

```bash
PYTHONPATH=src:shared/runtime pytest -q \
  generators/e3a2ff6ea587/tests/test_parametric_triggered_cascade.py
PYTHONPATH=src:shared/runtime python \
  generators/e3a2ff6ea587/workspace/parametric/adversarial_probe.py
```
