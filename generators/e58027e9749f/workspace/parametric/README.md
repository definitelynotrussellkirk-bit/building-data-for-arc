# Proposed diagonal reflection parameter — prototype only

This task-local experiment preserves the family reasoning: keep the colored
sources and copy them across a diagonal of a square grid. It does not change
`generator.py`, the canonical rule, the catalog, approval identities, or any
shared runtime interface. The production generator still has one fixed rule.

## Parameter and executed programs

`reflection_axis` has exactly two allowed values:

| Setting | Copy coordinate on an n-by-n grid | Executed expression |
| --- | --- | --- |
| `main_diagonal` (original/default setting) | `(r,c) -> (c,r)` | `(overlay g (transpose g))` |
| `anti_diagonal` (proposed alternative) | `(r,c) -> (n-1-c,n-1-r)` | `(overlay g (rotate-180 (transpose g)))` |

`render_program()` emits a commented `(rule! (lambda (g) ...))` program for each
setting. The original expression is unchanged. `execute()` removes only the
existing `rule!` authoring marker and comments using the included normalizer,
then applies the materialized lambda through the included real `RacketBridge`.
There is no Python label mirror. This small explicit-lambda path avoids the
raw checkout's legacy `scripts` import needed by the general shorthand wrapper.

`generate_episode(seed)` draws the setting **once** using a local seeded RNG,
then keeps the same Racket program for every demonstration and query. Supplying
`reflection_axis` pins that one episode's setting, useful for comparisons.
The CLI without `--axis` deliberately retains one episode for each setting.
Each episode has three demonstrations and two queries by default. Counts may
be set through the Python API to integers in 1..10; smaller demonstration
counts still distinguish the two declared settings.

## Runnable commands

From the packet's `WORK/` directory, using a new output directory:

```bash
python3 run_with_racket.py python3 generators/e58027e9749f/workspace/parametric/prototype.py --seed 23 --out ../checks/parametric/reproduction-s23
```

To retain only the alternative, add `--axis anti_diagonal`. With the included
Racket executable already on `PATH` or named by `RACKET_PATH`, it is also
possible to run the script directly from `WORK/repo/`:

```bash
python3 generators/e58027e9749f/workspace/parametric/prototype.py --seed 23 --out ../checks/parametric/reproduction-direct-s23
python3 -m pytest -q generators/e58027e9749f/tests/test_parametric_reflection.py
```

The final command requires pytest; the prototype itself uses the Python
standard library and the included Racket runtime/bridge. No predecessor or
sibling checkout is imported. All relative module locations derive from this
checkout. Ordinary repositories use `shared/runtime`; official staged snapshots
with `RUNTIME_MANIFEST.json` use their execution dependencies at the runtime
root. The repository mirror in such a snapshot must not shadow those packages.

## Input constraints and identifiability

Both settings use the same conservative input distribution: square grids of
size 4..10, background zero, colors 1..9, and one to grid-size source cells.
Sources avoid **both** diagonal fixed points. For either reflection axis, no
source's reflected target is already occupied by another source. This avoids
color conflicts and keeps every original cell intact. These are prototype
constraints, not a claim that canonical inputs require avoidance of both axes.

All candidate labels for **both** settings are executed in Racket. A draw is
accepted only if their complete outputs differ, with an explicit cap of 100
attempts per pair. Consequently every demonstration in the retained episodes
refutes the other declared setting before a query needs that distinction.
This also avoids ambiguous queries in this bounded experiment. Only these
two parameter rivals are checked; this is not an exhaustive search over
arbitrary transformations a solver could invent.

## Retained evidence and separation

`WORK/checks/parametric/episodes-s23/` contains two complete episodes, one per
setting. For each neutral numeric index:

- `public-N.json` contains only training input/output pairs and query inputs.
- `private-N.json` records the seed, hidden choice, query labels, exact program
  and its SHA-256, and the other setting's actually executed outputs.
- `program-N.rkt` is the exact emitted program used for that episode.

Only `public-N.json` is a public challenge. Keep the private files, programs,
receipt, and witness outside a solver's challenge payload. `witness.json`
retains a four-by-four input with a single color-7 source at `(0,1)`:
main-diagonal reflection adds `(1,0)`, while anti-diagonal reflection adds
`(2,3)`. The outputs were obtained by running both materialized Racket programs.
`receipt.json` binds seed 23, the **prior** prototype/test source hashes,
command arguments, program provenance, runtime identity, and finite limitations.
Those original CLI receipts were not regenerated after the import portability
fix. They remain valid evidence for prototype SHA-256
`6dbaf275a6357b81050e23785a09a85d1b0facd322df2fff1d75d564e1a72d76`,
whose exact bytes are retained in
`WORK/checks/parametric/prior-prototype-before-portability.py`. The portability
change only selects the appropriate local dependency root; it does not change
materialized Racket programs, sampling, or output/public-private semantics.
Do not describe the old CLI receipt as binding the current source. The final
official task-test stage and fresh-return replay must supply current-source
integration evidence.

`WORK/checks/parametric/red.log` records the five initial expected test failures
before implementation. `cli-red.log` records the independently caught CLI
runtime-identity property bug before its fix. `green.log` records the prior
six-test result, covering explicit expected outputs, episode-fixed choice,
repeatability, executed labels, declared parameter rival elimination,
collision constraints, invalid arguments, and public/private export separation.
The additional staged-layout regression imports the prototype in a fresh
process with actual execution-layout dependencies, a copied repository mirror,
and the genuine `reviewer_support.load_selected_generator`. It reproduces the
source-tree contamination failure before the fix and verifies that both imports
cooperate after the fix, without starting Racket or clearing module caches.
`portability-red.log`, `portability-green.log`, `portability-source-before.json`,
and `portability-fix.json` record this change. The initial official integration
failure is retained separately under `WORK/checks/task-tests-private/`: the
prototype's six tests passed but all reflection tests errored during setup.
That failed integration is not superseded by pretending the old test run passed.
The initial resolved execution failures remain in
`first-green-environment-failure.log` and `episodes-initial-cli-failure.log`.
`commands.json` records the actual commands and statuses.

These tests concern the **prototype only**, separately from canonical generator
repair coverage. Retained evidence includes seed 23 for both settings and seed
5 in the reproducibility test; it is finite evidence, not proof over all seeds,
all possible inputs, or richer parameter families. No alternative has production
approval, and no production parametric-rule API is proposed by these files.
