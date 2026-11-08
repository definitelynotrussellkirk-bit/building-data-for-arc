# Proposed `corner_basis` parameter

This isolated prototype preserves the tiny-L object grammar, component colors,
enlargement factor, and large border-L rendering. It changes one episode-level
rule choice:

- `corner_basis = elbow` is the original/default canonical behavior: the occupied
  elbow of each 2×2 L chooses the corresponding output corner.
- `corner_basis = missing` is the proposed nearby variant: the missing vertex of
  the same 2×2 bounding box chooses the output corner.

The parameter is selected once from the deterministic episode seed and stays
fixed across all demonstrations and queries. Complete episodes use incomplete
orientation sets or distinct object colors, so every demonstration distinguishes
the two opposite-corner mappings. Public challenge files retain training labels
but omit the hidden parameter, exact programs, provenance, and query answers.

Run focused tests from the outer extraction directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/3ab9aab86992/tests/test_review_20261021.py \
  generators/3ab9aab86992/tests/test_parametric_corner_basis.py
```

Materialize both exact Racket settings and complete episodes:

```bash
python3 review.py run python3 \
  generators/3ab9aab86992/workspace/parametric/prototype.py \
  --out ../checks/parametric
```

The retained report is `WORK/checks/parametric/evidence.json`. Exact Racket
programs are under `rules/`, private complete episodes under `private/`, and
redacted challenges under `public/`. This is a **proposed prototype**, not a
production API, canonical-rule change, approval, or training-admission claim.
