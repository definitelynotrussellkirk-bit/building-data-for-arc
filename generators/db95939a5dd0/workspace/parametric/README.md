# Proposed shift-distance prototype

This isolated authoring prototype keeps the canonical `db95939a5dd0` reasoning
structure and varies one hidden episode-level parameter:

- `shift_distance = 1` — original/default canonical behavior.
- `shift_distance = 2` — proposed nearby behavior.

The upper colour of every two-colour vertical compound moves left by the fixed
episode distance; the lower colour moves right by the same distance onto a
fresh mode-colour canvas. Prototype inputs reserve two columns of horizontal
clearance, so both settings are legal and collision-free. The setting is chosen
once from the episode seed and shared by three demonstrations plus one query.
Every demonstration distinguishes 1 from 2.

From the outer packet extraction directory:

```bash
python3 review.py run python3 \
  generators/db95939a5dd0/workspace/parametric/prototype.py \
  --out-dir /absolute/path/to/WORK/checks/parametric
```

The command refuses to overwrite evidence. It materializes both exact Racket
programs, checks distance 1 on all labeled canonical pairs, executes every
retained episode label and a counterfactual witness through bundled Racket,
checks Python-mirror parity, and writes private/public outputs separately.
This is **proposed prototype evidence**, not production authority or approval.
