# Scaled template assembly

Run from the packet's outer folder, with its installed Python and Racket runtime:

```sh
python3 review.py run python3 -m pytest -q generators/public_eval_898e7135/tests
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_898e7135 --root . --out ../checks/public_eval_898e7135/preflight
python3 review.py run python3 generators/public_eval_898e7135/workspace/parametric/authoring.py audit --preflight ../checks/public_eval_898e7135/preflight/preflight.json --out ../checks/public_eval_898e7135/audit --census-seeds 128
python3 review.py run python3 generators/public_eval_898e7135/workspace/parametric/authoring.py verify-export --bundle ../checks/public_eval_898e7135/audit/preview
```

Use new output paths on reruns. Refresh the preflight after any code/test/program
change; all source hashes are checked again before and after auditing.
The generated preview is explicitly **unapproved authoring evidence**, because
native qualification/export requires owner registration. Give a model just one
hash-named JSON file from `preview/public/`, never the directory, manifest or
private data. A controller chooses the next file only after the preceding answer.
The same shuffled first view is used when stopping after one query.

`adapter.generate(seed, {'finish': setting}, demos, 4)` returns fresh private
labeled episodes. `family.public_view(episode, index)` serializes strictly the
demonstrations and selected query input; outputs, programs, settings and future
queries cannot influence those bytes. See notes.md for the admitted grammar and
bounded-evidence limitations. The source dictionary is task-local and relocatable.
