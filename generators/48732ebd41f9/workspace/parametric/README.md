# Proposed minimum-height rectangle family (prototype only)

This directory is isolated from the selected canonical execution path. It does
not change the approved Racket authority, canonical rule hash, or production
parametric API.

- Parameter: `minimum_height`
- Allowed values: `2`, `3`
- Canonical/default setting: `2`
- Episode selection: SHA-256 of task ID, parameter name, and seed modulo two;
  selected once and shared by all three demonstrations and the query
- Invariant reasoning: find the greatest-area all-zero axis-aligned rectangle
  whose height meets the episode threshold, then recolor exactly it with `6`
- Input constraint: every prototype scene has a unique low/wide two-row zero
  rectangle and a unique taller, smaller-area zero rectangle. Thus threshold 2
  selects the low/wide target while threshold 3 excludes it and selects the
  taller target.

The exact Racket programs are retained under `rules/`. The probe executes both
settings through the protected Racket bridge, checks an independent Python
mirror, builds one complete episode per setting, and checks the sole other
parameter value as a rival. Every labelled demonstration separates the settings.
Public challenge files omit the parameter, Racket program, and query answer.

Run from the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/48732ebd41f9/workspace/parametric/prototype.py \
  --seed-start 6200 \
  --out ../checks/parametric/minimum-height-evidence.json \
  --write-public generators/48732ebd41f9/workspace/parametric/examples
```

The evidence is deliberately bounded to two settings, two deterministic
complete episodes, and the declared threshold rival. It is a **prototype**, not
production approval and not a claim of uniqueness against undeclared rules.
