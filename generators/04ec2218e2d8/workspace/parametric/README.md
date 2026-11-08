# Parametric center-inset divisor — proposed prototype

This task-local prototype varies one episode-level rule parameter while preserving
the original task's object roles and reasoning structure.

| Parameter | Allowed values | Executed inset rule | Original/default |
| --- | --- | --- | --- |
| `inset_divisor` | `4` | `t = max(2, floor(min(h,w)/4))` | yes |
| `inset_divisor` | `3` | `t = max(2, floor(min(h,w)/3))` | no |

The rule still finds each 4-connected cyan object, computes its own bounding box,
leaves non-object cells untouched, paints the inset center yellow, and paints the
remaining ring by the same top-left/top-right/bottom-left/bottom-right palette.
Divisor `3` makes the quadrant ring thicker (and the yellow center smaller) on
medium and large objects. The `4` program is the selected canonical Racket text
byte-for-byte.

One setting is chosen deterministically from the episode seed and remains fixed
for all three demonstrations and the query. Controlled inputs use the selected
production generator and include at least one component with minimum bbox side
`>= 9`; this is necessary because 6–8-cell sides make the two formulas coincide.
Every retained demonstration and query distinguishes the two declared settings.
Labels and rival outputs are produced by executing the exact materialized Racket
programs through the included protected bridge, not by a Python output mirror.

Run from the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/04ec2218e2d8/workspace/parametric/prototype.py \
  --seed 481 --out ../checks/parametric/inset-gallery

python3 review.py run python3 -m pytest -q \
  generators/04ec2218e2d8/tests/test_parametric_inset.py
```

The gallery contains two complete private episodes, masked public challenges,
exact `.rkt` programs and hashes, a shared-input setting-difference witness, a
canonical-default replay check, generator/source hashes, runtime identity, and a
summary report.

This is a **proposed prototype**, separate from the fixed-rule production generator.
It does not modify the selected generator or canonical authority, and it carries no
approval or training-admission claim. Evidence is finite: two settings, two episode
seeds, four controlled inputs per episode, and only the opposite divisor as a
parameter rival.
