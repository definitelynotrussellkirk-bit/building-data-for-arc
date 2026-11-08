# Workspace: 99f58784e7a0

The selected implementation is `../generator.py`. These reusable probes are independent review tools; they are not imported by production generation.

## `reference_probe.py`

An independent connected-component/chamber oracle. It reconstructs full color-8 wall rows and columns directly from pixels, validates chamber structure, fills each chamber without calling production helpers, and exposes canonical pairs through the packet's portable authoring helper.

Used by the task-local tests to avoid circular “generator agrees with itself” evidence.

## `curriculum_probe.py`

A bounded deterministic curriculum stress test. It checks:

- all five canonical pairs against the independent oracle;
- 256 default samples per difficulty band;
- validator and oracle agreement;
- support for all declared axis values;
- all 64 exact override/band combinations;
- all 96 cyclic query rotations of the four-sample schedule;
- agreement between the production and independently written `distinct_colors_only` rival.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/99f58784e7a0/workspace/curriculum_probe.py \
  --out ../checks/curriculum-probe.json
```

The retained final report is `checks/curriculum-probe-final.json` and binds itself to both generator and probe SHA-256 values.

## Scope

These probes establish correctness over the declared rectangular-chamber grammar and finite rival set. They do not claim universal ARC identifiability or support for partial/nonrectangular walls.
