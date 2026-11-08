# Task-local review tools

## `orbit_integrity_probe.py`

A source-bound, self-check-independent census for this task's geometric failure
mode. It records the audited source SHA-256 and counts:

- source cells whose four-position rotational orbit is clipped;
- two or more source cells that own the same orbit;
- the subset of duplicate orbits with different colors; and
- grids whose every source cell has a complete, unique orbit.

Run the current generator from the repository root:

```bash
PYTHONPATH=shared/runtime:. python3 \
  generators/8c069ab108a1/workspace/orbit_integrity_probe.py \
  --draws-per-band 1000 --out ../checks/orbit-integrity-after.json
```

Audit a retained historical source without replacing the current generator:

```bash
PYTHONPATH=shared/runtime:. python3 \
  generators/8c069ab108a1/workspace/orbit_integrity_probe.py \
  --source ../checks/intermediate-sources/generator-v1.2.0-baseline.py \
  --draws-per-band 1000 --out ../checks/orbit-integrity-before.json
```

The probe intentionally does not call `self_check`, so a source cannot make the
metric disappear by weakening its own validator. Its domain is the ordinary
sampler and this task's four-rotation geometry; it is not a universal ARC gate.
