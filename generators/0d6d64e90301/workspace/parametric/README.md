# Proposed parametric upscale family (prototype only)

This directory is separate from the selected canonical execution path. It does
not change the approved source, rule hash, or production generator.

- Parameter: `scale_factor`
- Allowed values: `2`, `3`
- Canonical/default setting: `2`
- Episode selection: `ALLOWED_SCALE_FACTORS[seed % 2]`, once per episode
- Input constraint: non-empty rectangular ARC-color grids; retained examples
  stay close to the task's sparse connected two-color motif grammar.

Each setting has an exact standalone Racket program under `rules/`. The probe
builds two labelled demonstrations plus one query, executes both Racket settings
on every pair, checks the Python mirror only as a secondary assertion, and
verifies that every demonstration refutes the alternative scale factor.

Run from the outer packet directory so the bundled Racket runtime is selected:

```bash
python3 review.py run python3 \
  generators/0d6d64e90301/workspace/parametric/prototype.py \
  --seed 17 \
  --out ../checks/parametric/scale-factor-seed17.json \
  --write-public generators/0d6d64e90301/workspace/parametric/examples
```

The generated `*_public.json` files omit the hidden parameter and query answer.
The retained evidence is bounded to two settings and one episode seed; it is not
production approval and does not establish uniqueness against undeclared rules.
