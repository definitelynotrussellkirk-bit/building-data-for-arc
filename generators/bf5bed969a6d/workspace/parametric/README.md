# Native template-orientation family

This directory contains the source-qualified parametric adapter for
`bf5bed969a6d`. The canonical setting, `template_transform="as_is"`, preserves
the selected Racket program exactly. The alternate setting,
`template_transform="rotate_cw"`, rotates the input-derived color-2 template
90 degrees clockwise before stamping a frame-colored copy into each target
component.

## Contract

- Settings: `as_is` and `rotate_cw`.
- Default: `as_is`; `canonical.rkt` is byte-for-byte the canonical authority.
- Demonstrations: any prefix of 2–6.
- Queries: any prefix of 1–4; qualification uses four.
- Inputs are deterministic, count-prefix stable, and independent of the hidden
  setting.
- Shapes vary through asymmetric templates, D4 input orientations, colors,
  disjoint and overlapping frame components, canvas dimensions, and occlusion.
- Query four is a substantive 30×30 case with 161 nonzero cells and four
  same-color components after overlap.

The rule has a non-collapsing sequential dependency. Step A extracts the unique
color-2 connected component, normalizes its offsets, and applies the selected
orientation transform. Step B uses those offsets and their transformed height
and width to center and recolor the stamp inside every non-template component.
The retained `wrong-fixed-template.rkt` ablation replaces the input-derived
intermediate with a fixed L; protected-Racket replay changes qualified labels
for both settings.

## Reproduce

From the extracted packet root:

```bash
python3 review.py run python3 generators/bf5bed969a6d/workspace/parametric/audit.py \
  --out ../checks/bf5bed969a6d/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify bf5bed969a6d \
  --demos 2 --queries 4 --out ../checks/bf5bed969a6d/qualification --summary
python3 review.py run python3 -m arcpuzzles.review_witness check \
  --qualification ../checks/bf5bed969a6d/qualification/qualification.json \
  --witness ../checks/bf5bed969a6d/causal/witness.json \
  --out ../checks/bf5bed969a6d/causal-recheck.json
```

`audit.py` checks 32 seeds, demo counts 2/3/6, both settings, declared-setting
confusion, six additional semantic shortcut rivals, determinism, count-prefix
stability, setting-independent inputs, and the 30×30 boundary. It also executes
32 adapter labels through protected Racket. Native qualification separately
executes two fresh seeds per setting with two demonstrations and four queries.

The existing task test was also made relocatable by using
`reviewer_support.find_root` and `canonical_path` rather than a fixed parent
count; this changes no generator or canonical behavior.

## Status and limits

Reviewer qualification is ready and source-bound, but owner acceptance and
training admission are intentionally not performed here. The finite rival audit
and causal replay do not prove uniqueness against every possible program or
measured model-training gain.
