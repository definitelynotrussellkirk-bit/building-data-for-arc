# Geometry-derived socket docking

Run from the packet outer folder:

```sh
python3 review.py run python3 -m pytest -q generators/public_eval_8b9c3697/tests
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_8b9c3697 --root . --out ../checks/public_eval_8b9c3697/preflight
python3 review.py run python3 generators/public_eval_8b9c3697/workspace/parametric/authoring.py audit --preflight ../checks/public_eval_8b9c3697/preflight/preflight.json --out ../checks/public_eval_8b9c3697/audit --census-seeds 128
python3 review.py run python3 generators/public_eval_8b9c3697/workspace/parametric/authoring.py verify-export --bundle ../checks/public_eval_8b9c3697/audit/preview
```

Choose fresh output paths; refresh preflight after changing source or tests.
Native qualification, accepted-family exports and acceptance remain owner-only
after registration. These previews are explicitly unapproved authoring artifacts.
Send a model only one hash-named JSON file from preview/public/, not that directory
or any private file. The controller keeps the source permutation, answers,
settings and total query bank hidden. Stops after one query use the same first
public view as a continued four-query lesson.

`adapter.generate(seed, {'candidate_order': 'nearest'|'farthest'}, demos, 4)`
returns private labels. `family.public_view(episode, index)` strips all private
state and never inspects future queries or query answers. See notes.md for the
bounded grammar and real fixed defects; see causal/witness.json for exact programs,
intermediate geometry and protected counterfactual labels.
