# `61c0bcd32328` direction prototype

This directory is an isolated **proposed** extension. It does not change the
production generator API, canonical Racket authority, approval, or training
admission.

The episode-wide parameter is:

- `direction=clockwise` — the exact canonical Racket program, byte for byte.
- `direction=counterclockwise` — the same component extraction, corner test,
  copy/preserve behavior, and colors, with only the adjacent-corner translation
  table reversed.

The setting is chosen once from the episode seed and held fixed across all
pairs. Inputs are independent of the setting. Three demonstrations include a
singleton-corner witness and refute both the opposite direction and the retained
"ignore singleton corner objects as noise" shortcut. Four distinct queries are
labeled through the matching Racket program. Public filenames are SHA-256 IDs of
only the visible demonstrations and query inputs; parameters, seeds, programs,
and query answers stay private.

From `WORK/`, generate immutable evidence for both settings:

```bash
python3 run_with_racket.py \
  python3 generators/61c0bcd32328/workspace/parametric/prototype.py \
  --seeds 0 1 \
  --train 3 \
  --test 4 \
  --difficulty medium \
  --out ../checks/parametric/61c0bcd32328-direction-v1
```

The command refuses to overwrite an existing directory. Current bounded support
is one to ten total pairs because the prototype uses ten distinct declared
corner-profile slots rather than cloning inputs.
