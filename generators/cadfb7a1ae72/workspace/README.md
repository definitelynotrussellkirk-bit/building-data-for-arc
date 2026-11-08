# Workspace diagnostics

The selected implementation is `../generator.py`. This workspace contains reusable diagnostics, not alternate selected code.

## `inspect_features.py`

Inspect a generated scene, a canonical pair, or a JSON grid. The report lists each top-left-ordered object's color, bounding box, area, connected hole-region count, total enclosed zero-cell area, exact reflection class, and projection-derived reflection class. It then prints the intended relation matrix and every declared rival matrix with the first disagreement.

```sh
PYTHONPATH=shared/runtime python3 generators/cadfb7a1ae72/workspace/inspect_features.py \
  --seed 1234 --sample-index 3 --difficulty medium

PYTHONPATH=shared/runtime python3 generators/cadfb7a1ae72/workspace/inspect_features.py \
  --canonical 0
```

Retained exact reports:

- `example_projection_report.json`: identical ordered row/column projections with different exact reflection classes; seed `1234`, sample index `2`, difficulty `medium`.
- `example_binary_holes_report.json`: equal enclosed-zero-cell area with different connected hole-region counts; seed `1234`, sample index `3`, difficulty `medium`.

## `audit_curriculum.py`

Audit all declared atomic semantic rivals across sliding four-example lesson windows. The command also verifies that every entry labeled a canonical shortcut really fits every official pair; either stale canonical-fit metadata or a surviving rival makes the command fail.

```sh
PYTHONPATH=shared/runtime python3 generators/cadfb7a1ae72/workspace/audit_curriculum.py \
  --starts 200 --seed-base 71000 --out /tmp/cadfb-curriculum.json
```

## `audit_hypotheses.py`

Enumerate composed alternatives rather than changing one assumption at a time. The current finite family crosses:

- exact, axis-count, or projection-derived symmetry;
- connected regions, binary hollowness, or enclosed-cell count;
- top-left or ascending-color object order; and
- symmetry-first or holes-first precedence.

The tool retains only hypotheses that match every official pair, then reports whether any non-authority hypothesis survives a generated lesson window.

```sh
PYTHONPATH=shared/runtime python3 generators/cadfb7a1ae72/workspace/audit_hypotheses.py \
  --starts 200 --seed-base 91000 --out /tmp/cadfb-hypotheses.json
```
