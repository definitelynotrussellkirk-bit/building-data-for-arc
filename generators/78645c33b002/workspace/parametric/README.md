# Nested-ring thickness: proposed parametric prototype

**Status: proposed prototype; not production-approved.** This workspace experiment does not alter the selected canonical Racket authority, catalogs, approval state, or training admission.

## Parameter

`ring_thickness` is chosen once per episode from the bounded set `{1, 2}`.
The default value `1` returns the exact canonical Racket program bytes. Value
`2` keeps the same reasoning—extract ordered colors of nested filled rectangles
and normalize them as concentric square layers—but makes every noncentral output
ring two cells thick. The center remains one cell. No input constraint depends
on the parameter.

For `K` input layers, setting `t` produces side length
`2*t*(K-1)+1`. Thus every lawful input with at least two layers distinguishes
the two settings by output size as well as cell layout. The retained episodes
contain three demonstrations and one query; every demonstration is checked
against both Racket programs, and only the selected setting matches its labels.
The parameter is hidden at challenge time and must be inferred from the
examples.

## Run

From the extracted review directory:

```bash
python3 review.py run python3 generators/78645c33b002/workspace/parametric/prototype.py \
  --seeds 1 0 --out ../checks/parametric/episodes
```

Focused unit tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/78645c33b002/tests/test_parametric_ring_thickness.py
```

The output separates model-visible `public/` challenges from evaluator-only
`private/` evidence and exact `rules/` sources. The private manifest records
parameter values, source and rule hashes, exact Racket application expressions,
all candidate outputs, runtime identity, commands, and limitations.

## Scope and limits

This is a two-setting authoring prototype over the selected generator's current
nested-rectangle input grammar. It is not a production parametric API and makes
no all-seed or universal-identifiability claim. Finite demonstrations reject the
declared thickness rival only; other invented rules remain outside the bounded
check.
