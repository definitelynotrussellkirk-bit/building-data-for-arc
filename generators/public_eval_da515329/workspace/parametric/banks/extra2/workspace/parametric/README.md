# Cropped interlocking-spiral family

`finish=spiral_only` is byte-identical to `reference.rkt`. Four equal radial
arms seed four rotations of one infinite square-spiral branch; rendering crops
the completed construction to the input canvas. `finish=highlight_most_visible`
counts the in-bounds cells of each completed branch and recolors the unique
largest visible branch 9.

The causal counterfactual in `wrong-intermediate.rkt` substitutes a fixed north
branch for the post-construction visible-count argmax. The sampler searches a
small deterministic placement bank whose four visible counts are all distinct.
The minimum two-demo lesson schedules different winning branches.

Run focused tests from the repository root:

```bash
python3 -m pytest generators/public_eval_da515329/tests -q
python3 generators/public_eval_da515329/workspace/parametric/authoring.py --out /tmp/spiral-audit.json
```
