# Proposed `hole_selection` rule parameter

This directory is a **prototype**, not a production or approved rule change.
The selected generator still uses the canonical `all_holes` Racket authority.

The bounded parameter is chosen once per complete episode:

- `all_holes` — canonical/default; carve every enclosed local zero region.
- `largest_hole` — proposed alternative; carve only the largest region.

Prototype inputs use a 5×5 framed template with two unequal enclosed holes.
Both demonstrations in every retained episode make the settings disagree, so
learners do not need to guess the hidden value at query time.

From `WORK/`, materialize and verify the retained evidence with:

```bash
python3 run_with_racket.py python3 generators/bc932ac8117a/workspace/parametric/prototype.py materialize \
  --out generators/bc932ac8117a/workspace/parametric
```

Run focused tests with:

```bash
python3 run_with_racket.py python3 -m pytest -q \
  generators/bc932ac8117a/tests/test_parametric_prototype.py
```

Artifacts:

- `rules/*.rkt`: exact materialized Racket programs.
- `episodes/*.json`: complete Racket-labelled episodes, including private query outputs.
- `challenges/*.json`: public views with hidden parameter and query outputs removed.
- `evidence.json`: source/rule hashes, seeds, rival disagreements, and limits.

The `largest_hole` setting excludes ties by construction. Broad production
integration, schedule design, approval, and arbitrary-seed validation remain
out of scope.
