# Length-ranked rod family

`finish=rank_only` is byte-identical to `reference.rkt`. The detached legend's
multiplicity for each endpoint color selects that color's rod after sorting by
payload length, longest first. `finish=highlight_longest_selected` first performs
that complete selection and then recolors the complete longest selected rod 9.

The causal counterfactual in `wrong-intermediate.rkt` skips the legend-selected
set and highlights the globally longest raw rod. The constructive sampler makes
that raw rod unselected and gives all selected rods distinct lengths.

Run focused tests from the repository root:

```bash
python3 -m pytest generators/public_eval_97d7923e/tests -q
python3 generators/public_eval_97d7923e/workspace/parametric/authoring.py --out /tmp/sticks-audit.json
```
