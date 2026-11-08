# Gravity distribution diagnostic

The selected implementation is [../generator.py](../generator.py).
[probe_distribution.py](probe_distribution.py) is a reusable, finite Python
diagnostic for that source and its declared rivals. It uses an independent
adjacent-swap compaction procedure, checks the five supplied canonical pairs,
records distribution counts, and scores every query holdout of overlapping
raw-index windows. It does not execute Racket labels or the production
materializer, and it does not draw assignments or audits.

## Run from the packet

From `WORK/`, use a new report path:

```bash
python3 run_with_racket.py python3 generators/2a43e4f3a796/workspace/probe_distribution.py --seeds 100 --indices 5 --train 4 --out ../checks/distribution-rerun.json
```

`--train` defaults to the selected source's positive integer `EXAMPLES_NEEDED`
declaration, currently four, with a fallback of three when that declaration is
absent or invalid. `--indices` counts both marginal sample indices and window
starts. Extra generated indices complete the overlapping windows and are
excluded from the marginal denominator. `--source` accepts an absolute path to
a retained generator for an explicitly marked comparison. The report binds
source, probe, canonical program identity, arguments, input hashes, and any
smallest complete failing window. Python outputs in this report remain
diagnostic even when the wrapper supplies an available Racket runtime.

## Retained final evidence

The selected `3.1.0` source SHA-256 is
`6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9`;
the probe SHA-256 is
`aadc6a2c903178c5663a3a1f87afae5fecf7ddc022911dbfe14707ac52f67828`.

| Artifact | Scope |
|---|---|
| [Distribution report](../../../../checks/distribution-v31.json) | 100 seeds, five starts, three bands: 1,500 windows and 7,500 rotations; all eleven distinct rivals refuted in every rotation. |
| [Code review](../../../../checks/final-code-review.json) | Final source/probe/test hashes, exact probe command, construction reasoning, and bounded witness checks. |
| [Racket lesson census](../../../../checks/lesson-census-v31.json) | Separate production materialization: 300 lessons, 1,500 unique inputs, and 1,500 rotations, with no listed-rival ambiguity. |
| [Schedule census](../../../../checks/schedule-census-v31.json) | All period-five starting residues at seed zero in three bands: 15 lessons, 75 pairs/rotations, and nine globally unique inputs. |
| [Required-rotation check](../../../../checks/required-rotations-v31/result.json) | 12 actual materialized lessons and 60 rotations pass the required semantic policy against declared rivals. |
| [Racket witnesses](../../../../checks/final-witnesses/comparison.json) | 18 actual label matches: 12 authored endpoints/counterexamples plus six ordinary dense/sparse samples. |
| [Portable tests](../../../../checks/task-tests-isolated-v31/result.json) | 60 passed with retained interpreter and runtime provenance. |
| [Interaction finding](../../../../checks/interaction-before/review_evidence.json) | Superseded-source conditional-cap counterexample and historical diagnostics; not final-source checks. |

The ordinary schedule is `dense, sparse, dense, sparse, free`; an arbitrary
holdout leaves both teaching types in four demonstrations. This construction
argument and the finite rival checks have different scopes from production
filtering and from universal rule identification. Exact override lessons need
their own checks. Current unresolved audit and battery findings are documented
in [../notes.md](../notes.md); none of these artifacts grants training admission.
