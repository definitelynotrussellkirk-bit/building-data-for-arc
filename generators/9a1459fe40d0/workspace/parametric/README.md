# Folded-XOR mark-policy parametric family

This task-local native family exposes one episode-fixed setting:

| `mark_policy` | Rule |
| --- | --- |
| `project_right` | Exact canonical program: mark each occupancy-XOR pair at its reflected right-half coordinate. |
| `occupied_side` | Use the same occupancy-XOR classification, but mark the coordinate that is actually occupied. |

The canonical setting returns the selected authority bytes exactly. Both settings
ignore payload colors when testing occupancy, return a fresh zero grid, and leave
doubly occupied mirror pairs unmarked even when their colors differ.

## Sequential dependency

1. **A:** locate the full-height cyan divider and classify every mirror pair as left-only, right-only, doubly occupied, or empty.
2. **Intermediate:** the ordered directed-XOR records, including each mismatch's occupied coordinate.
3. **B:** render orange marks using either the projected-right or occupied-side target from those records.

For `occupied_side`, collapsing the intermediate to an undirected mismatch mask
loses the required side. The retained protected-Racket counterfactual projects
all mismatches right and changes the qualified maximum-size output.

## Sampling and public projection

`generate(seed, settings, demos, queries)` supports 2–6 demonstrations and 1–4
queries independently. Inputs are matched across settings and prefix-stable as
counts change. Every scene contains left-only and right-only mismatches plus
same-color and different-color doubly occupied controls. The four query sizes are
14×21, 20×25, 26×27, and 30×29. Width 30 is not lawful for equal halves separated
by one center column; 30×29 is the maximum natural stress surface and contains
substantial payload across the canvas.

`public_turn(episode, index)` returns all demonstrations and exactly one unlabeled
query without settings, programs, answers, future queries, indices, or total-count
hints. `audit.py` checks twelve executable finite rivals across seeds and supported
demonstration boundaries. This finite audit does not prove universal uniqueness.
Owner acceptance and training admission remain separate from reviewer qualification.
