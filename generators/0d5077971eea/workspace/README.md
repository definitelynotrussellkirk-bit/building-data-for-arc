# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Independent authoring checks

`review_support.py` loads the generator from this task tree (or the explicit
`GENERATOR_UNDER_TEST` path), locates the public portable canonical-data helper,
and implements an independent row recoloring oracle. It imports no private runner
helpers. These files are authoring data with answers and are closed during solves.

The task tests cover all 1,680 joint axis tuples in each of None/easy/medium/hard
(6,720 constructive instances), a 10,000-seed capacity sweep on the smallest
canvas with the full ten-color palette at high density, strict invalid overrides, canonical acceptance,
the actual canonical rival declarations, preserved foreign spectators and
zero/header-8 cases, determinism, productive output, and cyclic three-demo windows
for both one and two queries. Execute from the extracted packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 0d5077971eea --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

`census_rotations.py` extends retained public Racket-backed census evidence to
every cyclic three-demo window in each saved complete lesson. All remaining
pairs become queries. It scores the generator's actual declarations dynamically
in all three namespaces, checks the final generator bytes against the census,
verifies saved instance hashes, and rechecks canonical rival fits. It retains
source hashes, exact unique-input hashes, per-band/window counts and complete
counterexamples for any measured ambiguity. It does not regenerate lessons.

```bash
python3 run_with_racket.py python3 generators/0d5077971eea/workspace/census_rotations.py --census ../checks/lesson-census.json --out ../checks/census-rotations.json
```

Use fresh output paths on reruns. Exit 0 means completed evidence with no declared
ambiguity or hook warning, 1 means ambiguity/warnings, and 2 means an error.
This finite probe does not establish universal identifiability. The four minimal
regressions were first run against v1.2.1; their actual failures are retained at
`checks/regression-before.log` in the packet.

## Retained regression iterations

Log names containing `final` below describe earlier completed test runs and are
superseded where this table says intermediate. Source hashes distinguish the
populations; earlier successes are not measurements of later generator bytes.

| Packet evidence | State and measured result | Generator SHA-256 |
|---|---|---|
| `checks/regression-before.log` | Baseline: four regressions failed | `315c7676bc7a70900a85fe823a93926cd2e641ffe659146d79d5a47ff98cb991` |
| `checks/regression-intermediate.log`, `checks/intermediate-cyclic-witnesses.json` | Intermediate: 45 passed, six cyclic-window failures; witnesses use independent oracle labels | `73341ec83ebe6350902a4c5d6bcc503865e7dd3d28a0c8f2d5dedb7dc4422b0b` |
| `checks/regression-final.log` | Intermediate: 51 passed before capacity defect was found | `8b37e5215e4db012ba7d055160cbd14661faba9076009f2abf18c7a8b1033edb` |
| `checks/regression-final-with-probe.log` | Intermediate: 53 passed before capacity defect was found | `8b37e5215e4db012ba7d055160cbd14661faba9076009f2abf18c7a8b1033edb` |
| `checks/regression-capacity-before.log` | Intermediate: seed 6127 exact joint override exhausted palette capacity | `8b37e5215e4db012ba7d055160cbd14661faba9076009f2abf18c7a8b1033edb` |
| `checks/regression-final-v2.log` | Final generator: 54 passed; probe self-test assigned an unchanged cell value, so its intended corruption was ineffective | `a338b592c839a0ef4bec46d972da6ca06e45f2caf0353869343902badc5b3f61` |
| `checks/regression-final-v2-verified.log` | Final generator: 55 passed after the probe test guaranteed a changed cell | `a338b592c839a0ef4bec46d972da6ca06e45f2caf0353869343902badc5b3f61` |

The final suite checks 6,720 exact joint-axis instances, the 10,000-seed minimum
canvas capacity sweep, and 648 overlapping cyclic windows from 144 independently
assembled lessons (72 with one query and 72 with two). Those generated checks use
the independent row oracle. Authoritative public battery/census reports are kept
separately by the review controller.
