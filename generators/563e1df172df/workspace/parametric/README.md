# Proposed prototype: endpoint-path turn order

This separate task-local prototype adds one bounded rule parameter:

| Parameter | Allowed values | Default / original |
|---|---|---|
| `turn_order` | `horizontal_first`, `vertical_first` | `horizontal_first` |

Both settings locate the unique red (`2`) start and green (`3`) destination,
preserve those endpoints, and paint an axis-aligned L using color `8`.
`horizontal_first` bends at `(red row, green column)` and uses the exact selected
canonical Racket text. `vertical_first` bends at `(green row, red column)`.
The parameter changes the executed transformation, not the input distribution.
All input constraints are invariant: rectangular black background, one red and
one green on different rows and columns. Inputs come directly from the existing
selected generator, with its difficulty and sample-index schedule.

A complete prototype episode has **four demonstrations and one query**. The
parameter is fixed once before any inputs are drawn and reused for every pair.
`build_episode(seed)` defaults to the canonical setting; pass
`turn_order='vertical_first'` for the alternative. Passing `turn_order=None`
uses `select_turn_order(seed)` to choose once through stable SHA-256. Every
lawful input distinguishes the two elbows, so the other setting is rejected by
every demonstration. This checks exactly the two declared parameter settings;
it does not inherit the production generator's larger competitor set, lesson
length, curriculum claims, approval, or training admission.

## Exact runnable commands

Run from the extracted packet's `WORK/` directory, using the included Racket
wrapper. All payload paths and output paths are interpreted from `WORK/repo/`.
The payload needs Python 3.12+, NumPy and Pillow; testing additionally needs
pytest, as described in `repo/shared/README.md`.

```bash
.venv/bin/python run_with_racket.py "$PWD/.venv/bin/python" generators/563e1df172df/workspace/parametric/prototype.py --seed 173 --difficulty medium --start 0 --out ../checks/parametric/turn-order-s173

.venv/bin/python run_with_racket.py "$PWD/.venv/bin/python" -m pytest -q generators/563e1df172df/tests/test_parametric.py
```

The test command assumes the dependency environment is at `WORK/.venv`.
Use an absolute payload interpreter path because the wrapper changes directories.

Use a **fresh output directory** on each evidence run; existing directories are
refused. The CLI emits both settings on the same five input draws. Within the
result, `public/episode-000/challenge.json` and
`public/episode-001/challenge.json` contain only four labeled training pairs and
one unlabeled test input. They omit parameter values, reference source and query
answers. Keep the entire `private/` directory away from model-visible challenges.

Private manifests retain the seed, difficulty, indices, fixed parameters, all
query answers, exact materialized Racket text, exact and whitespace-normalized
rule hashes, selected-generator and prototype source hashes, rival predictions,
demonstration discrimination, a lawful same-input disagreement witness, all
canonical-pair default parity results, runtime preflight and executed command.
Actual retained run logs and command receipts live under
`WORK/checks/parametric/`; that evidence is separate from canonical repair checks.

Every example label and every rival prediction is evaluated by the included
`arc_repl.racket_bridge.RacketBridge`, with no private runner imports. A local
lexical identity binding for `rule!` unwraps the unchanged authoring form; its
lambda and grid primitives execute in the included Racket prelude. Neither a
Python mirror nor expected labels are used to generate outputs. Canonical parity
compares those executed outputs with every labeled canonical pair loaded by the
portable `reviewer_support.canonical_pairs` helper.

## Scope and limits

The prototype does not modify `generator.py`, the canonical rule, shared runtime
interfaces, catalog pins or production approval. It materializes both settings
at one bounded seed per CLI run. Focused tests also cover deterministic replay,
optional seeded parameter selection, literal parameter rejection, endpoint
retention, a hand-checked pair of elbows, and separation of private answers from
the public challenge. Finite rival discrimination establishes only that the
other declared setting cannot explain the retained demonstrations; arbitrary
unregistered shortcuts remain outside that claim.
