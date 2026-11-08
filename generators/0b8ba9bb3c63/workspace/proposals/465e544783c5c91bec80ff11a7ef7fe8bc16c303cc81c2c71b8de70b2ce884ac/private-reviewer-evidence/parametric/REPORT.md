# Parametric prototype handoff

**Status: tested proposed prototype.** The canonical generator and shared
runtime were not edited by this work. Install `workspace/parametric/` and
`tests/test_parametric.py` below the selected generator, then retain this
`checks/parametric/` directory in the review's checks tree.

## Implemented behavior

One rule parameter, `transparent_color ∈ {2,3}`, selects red or green as the
beam-transparent object role. Default `2` retains the exact canonical Racket
source bytes. All other original reasoning remains: cyan rectangular emitter,
yellow four-arm cross, per-row/per-column clipping, nearer opaque blockers,
opaque-object restoration, and transparent fragments outside the cross.
Both candidate colors occur in each scene. Paired seeds retain the same input
grids while changing the executable rule.

The prototype exposes demonstration and query counts independently, generates
distinct inputs, labels every pair through the protected Racket bridge, and
certifies each query against seven explicit Racket rules using demonstrations
alone. It writes a public challenge containing only train pairs and test inputs,
with private labels, parameters, programs, source hashes, runtime identity,
identifiability evidence, and artifact hashes in separate files.

## Actual verification

- **12 focused tests passed**, 10.629 seconds in the retained final unittest
  output. See `checks/parametric/tests.log` and
  `checks/parametric/test-command.json` for the exact command, working directory,
  interpreter and environment. Scope is the isolated prototype, including a real
  CLI invocation; it is separate from root's canonical repair battery.
- Default parity executed **all six unique official inputs** through both the
  independently loaded canonical authority and the prototype's default program,
  then checked both against supplied labels.
- Four retained CLI runs produced **32 Racket-labeled pairs**, including
  **16 query targets**. Every episode has four unique query inputs and no
  demonstration/query duplicate. Exact commands and stdout/stderr are in
  `checks/parametric/episode-commands.json`.
- All 16 queries pass demonstration-only declared-rival identifiability. Every
  episode has only its intended transparent-color setting compatible with all
  demonstrations. A no-demonstration control is explicitly ambiguous in tests.
- The default/alternative paired runs have identical inputs and different
  outputs on all 16 matched pairs. The retained first-demonstration witness
  differs in **38 output cells**; see
  `checks/parametric/parameter-witness.json`.
- All **44 artifact hashes** listed by the four episode manifests were
  independently rechecked after generation. Public challenge fields were
  independently whitelisted; current prototype source hashes were rechecked.
  See `checks/parametric/summary.json` for the assembled, source-bound evidence.

| Retained run | Setting | Seed | Demos | Queries | Input sizes |
|---|---:|---:|---:|---:|---|
| `checks/parametric/red-17/` | 2 | 17 | 3 | 4 | Demos 18×21, 17×20, 20×21; queries 18×30, 25×29, 28×20, 24×18 |
| `checks/parametric/green-17/` | 3 | 17 | 3 | 4 | Identical to red-17 |
| `checks/parametric/red-29-30x30/` | 2 | 29 | 5 | 4 | All 30×30 |
| `checks/parametric/green-29-30x30/` | 3 | 29 | 5 | 4 | All 30×30 |

The seed-17 queries all have a longer maximum side than every demonstration;
the same beam/clipping reasoning is executed at those larger sizes.

Exact rule SHA-256 values:

- Default 2: `e50f7da3fcaf4ab3b5de00698811e0e103c8e3f982755c9d8f5e2ff05165779d`
- Alternative 3: `560c6f92907922ec00017f54c41c4575d1be7c25d869b9725f3f55f4ed04bf69`
- Canonical normalized hash remains
  `757441c9ab4aa17070a3826de76e0b0f74e66636398f3f3aaa4392e47af17bcb`.

## Reproduce after installation

From `WORK/`:

```bash
python3 run_with_racket.py python3 generators/0b8ba9bb3c63/workspace/parametric/prototype.py --seed 17 --transparent-color 2 --demos 3 --queries 4 --out ../checks/parametric/red-17-replay
python3 run_with_racket.py python3 generators/0b8ba9bb3c63/workspace/parametric/prototype.py --seed 17 --transparent-color 3 --demos 3 --queries 4 --out ../checks/parametric/green-17-replay
python3 run_with_racket.py python3 -m unittest discover -s generators/0b8ba9bb3c63/tests -p test_parametric.py -v
```

Use fresh output paths. The original actual development commands, which used
absolute build paths while the task-local installation was pending, remain in
the command JSON receipts above. The runtime wrapper works with only
`shared/runtime` on PYTHONPATH. The task-local adapter resolves the normalizer's
`scripts` package only to the tools adjacent to the imported runtime; portable
runtime layouts already supply that package. The tests support both
`shared/data/` and copied `data/` canonical paths.

## Bounds and resolved development failures

Constructive input support is 17..30 on each side, with solid separated
rectangles and an intentionally bounded scene grammar. The original canonical
generator's 11..30 domain is unchanged. Counts are bounded to 1..32 each;
sampling fails visibly when its explicit budget is insufficient. Finite-rival
agreement does not prove identifiability against arbitrary programs. Nothing
here changes production API, safety approval, corpus difficulty, or admission.

Before implementation, the CLI regression failed as expected (1 failed,
11 skipped). The first implementation run then exposed the source-layout
`scripts.comment_solutions` dependency and the canonical JSON's wrapped query
input records. Those were corrected with a bounded source-relative adapter and
the proper authoritative input field. The retained final 12-test run passes.

Root still needs to run the stock task-test stage after installation and any
separately required canonical checks. This handoff does not claim those results.
