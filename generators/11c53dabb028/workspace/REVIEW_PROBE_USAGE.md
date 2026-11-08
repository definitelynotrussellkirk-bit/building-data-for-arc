# Semantic review probe

`review_probe.py` is task-local reviewer tooling. It supplies no generation
labels. Its diagnostic Python calculation complements one tile and concatenates
four copies; authority checks execute the selected canonical Racket source.

## Final-source run

Run from the extracted packet root after the shared census has completed on the
same generator bytes:

```bash
python3 run_with_racket.py python3 generators/11c53dabb028/workspace/review_probe.py --racket --per-band 100 --lesson-census ../checks/lesson-census-final.json --timeout 900 --out ../checks/semantic-review-final.json
```

The wrapper sets the effective working directory to `repo`; payload paths are
relative to that directory. The probe snapshots the selected runtime. It checks
the supplied census's task, completion state, generator hash, canonical source
hash, declaration names, five-demo/one-query shape, and each instance hash before
reusing its materialized pairs. A stale or incomplete census is an error.

The full report contains:

- All four canonical pairs, including independent diagnostic parity and the
  actual fit count of every declared canonical shortcut.
- The generator's current rival dictionaries, preserving all three namespaces.
  Repeated names across namespaces are repeated declarations, not independent
  hypotheses. The report does not hard-code the rival list.
- 180 independent default draws per difficulty band, with reproducible seed and
  sample-index recipes, validity, exact replay, selector roles, first-color
  support, shape diversity, and exact distinct-input counts.
- Every supplied five-demo/one-query lesson rotated into all six possible query
  positions. With 100 lessons per band, this means 1,800 query rotations over
  1,800 materialized pairs, not 1,800 independent lessons. Rival survival and
  actual query ambiguity remain separate outcomes.
- The complete product of both dimensions in `1..15`, density requests
  `0`, `0.5`, and `1`, both multicolor settings, and the default plus three
  difficulty bands: 5,400 requests. The expected fully specified domain has
  4,464 accepted tuples and 936 infeasible tuples. Accepted grids are counted
  independently from pixels and checked against real Racket outputs.
- First failures, actual source hashes, and the smallest observed input that
  refutes each rival. These are finite-sample minima, not global minimality
  proofs. Complete successful lesson instances remain in the shared census.

For direct Racket applications and the smaller standalone production sample,
the adapter uses public `RacketBridge` operations, the canonical source reader,
`wrap_rule`, public `GeneratorBundle` construction, and `runner.run_one`. It does
not import or call private runner helpers. `--python-only` is explicitly
diagnostic and never reports a Racket pass.

## Focused tests

```bash
python3 run_with_racket.py python3 -m pytest generators/11c53dabb028/tests/test_semantic_review.py -q
```

The suite includes every cyclic start and held-out query position, the complete
fully specified shape/density/multicolor product, loud rejection of invalid or
removed controls, exact regressions for the column-major construction defect,
and a small real-Racket production sample. The assignment's separate `task_tests`
stage additionally verifies relocation in its portable test snapshot.

The joint product binds both dimensions and density. It must not be described
as exhaustive coverage of partially specified override requests; those are
covered by the separate task contract regressions. Default lesson guarantees
also do not apply to explicit overrides.

## Retained cyclic counterexample

```bash
python3 run_with_racket.py python3 generators/11c53dabb028/workspace/review_probe.py --verify-counterexample generators/11c53dabb028/workspace/semantic_review_initial_failure.json --timeout 120 --out ../checks/cyclic-counterexample-reference.json
```

This mode makes one public `Catalog.apply` call for the six retained inputs.
It independently evaluates column-major selection and checks that the other
five pairs fit that rival while the held-out query disagrees. Reference-executor
generator provenance is not asserted to be the hash of the earlier producer;
the original raw probe did not capture that producer hash.

## Intermediate evidence

`semantic_review_intermediate.json` belongs to generator hash
`1d187923794f595699b40c024e5cbe44e95adf2c3608428a5de361ce022febe8`.
Its probe source hash is
`55f9680d4a822d2ecd332a78750d81398f95b896f8ad8afd4aadc5fc4a6aa11a`;
the exact probe bytes are retained in `checks/probe-intermediate.py` from the
packet root. Restore those bytes to the task workspace in the matching earlier
source tree when reproducing that run. The archived file is not intended to be
executed directly from `checks/`.

That run preceded the partial-override feasibility repair and the new
second-frequency shortcut repair. It remains intermediate evidence. The final
probe expects the revised witness design: middle-role first colors are
minorities, while minimum/maximum-role first colors are unique majorities;
every mixed default still separates first from last and column-major selection.
The command receipts retain original arguments and the post-run file renames.

The canonical examples contain square, single-foreground-color inputs. The
generated rectangle and multicolor evidence supports a broader interpretation
using the explicit unchanged rule. Finite checks against the declared rivals
do not establish universal induction, approval, or training value.
