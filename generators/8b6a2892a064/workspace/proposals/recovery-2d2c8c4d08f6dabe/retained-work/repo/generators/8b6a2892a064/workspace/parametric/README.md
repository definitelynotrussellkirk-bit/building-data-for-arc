# Proposed parametric prototype: selective centered line rotation

This is a task-local **proposed prototype**, separate from the selected
`generator.py`, the registered canonical Racket rule, and their approvals. It
does not change production interfaces, source/rule approval hashes, or training
admission. Its Python front end uses the standard library; actual labels and
finite rival predictions require the packet's included Racket bridge/runtime.

## Small rule variation first

The fixed reasoning is: identify the orange-7 canvas; find each isolated
four-connected foreground component; recognize its straight odd-length line;
locate the integer center; decide whether that object is selected; rotate
selected lines by 90 degrees about their own centers; preserve unselected
objects and colors; discard target cells outside the canvas. Singletons stay.

| Parameter | Allowed values | Original/default |
|---|---|---|
| `rotate_when` | `all`, `horizontal`, `vertical` | `all` |
| `min_length` | `3`, `5` | `3` |

A line rotates when both the orientation condition and the minimum length
condition hold. The default `all,3` has the canonical behavior on this family's
lawful inputs. All six combinations are retained. Selection changes executed
geometry, not just the input distribution. The same input-domain constraints
apply to every setting: rectangular ARC grids no larger than 30 by 30; orange
7 plus exactly one other color; four-connected objects that are contiguous
horizontal/vertical odd lines or singletons.

The sampler always includes horizontal lengths 3 and 5, vertical lengths 3 and
5, and one singleton. Its four corner zones preserve each line's distinguishing
cells under all six rules; edge placements can clip rotated target cells. A
central gap isolates the singleton. Dimensions (17–25), colors, zone assignment,
and centers vary. This is a deliberately bounded teaching distribution, not
the selected generator's named profile distribution. The executable rules and
domain validator also support other odd lengths, but the retained episode
coverage does not claim to sample them.

Each demonstration distinguishes all six settings. The prototype executes
every candidate on demonstrations, selects surviving settings using **only
demonstration labels**, and freezes that set before executing queries. Each
query then records its own surviving-settings check and five rejected rivals,
including their demonstration mismatch indices and Racket query predictions.
This is finite six-setting identifiability, not proof of unrestricted semantic
uniqueness or model learnability.

## Exactly four independent queries

From `WORK/`, run this exact retained-coverage command with a fresh output path:

```bash
python3 run_with_racket.py python3 generators/8b6a2892a064/workspace/parametric/prototype.py --seed 20261023 --all-settings --demos 3 --queries 4 --out ../checks/parametric/six-settings
```

This produces six complete episodes: 18 demonstrations and 24 queries in
total. Within each episode, all seven inputs are distinct. The same input
sequence across settings provides concrete lawful witnesses of their different
outputs. Parameter settings are fixed once at episode entry and are never
resampled per pair. `--demos` and `--queries` are independent controls; one
demonstration is sufficient for this sampler's declared six-setting family.

For the default canonical setting only:

```bash
python3 run_with_racket.py python3 generators/8b6a2892a064/workspace/parametric/prototype.py --seed 17 --demos 3 --queries 4 --out ../checks/parametric/default-setting
```

For a deterministic hidden setting sampled once from the episode seed:

```bash
python3 run_with_racket.py python3 generators/8b6a2892a064/workspace/parametric/prototype.py --seed 17 --sample-parameters --demos 3 --queries 4 --out ../checks/parametric/seeded-setting
```

For one fixed alternative, use `--rotate-when horizontal --min-length 5`.
The default remains `all,3`; seeded sampling is explicit. The parameter RNG
and layout RNG have separate deterministic streams. Sampling/all-settings
modes reject simultaneous fixed parameter overrides. No Python mirror supplies
any label: the exact lambda inside each emitted `rule!` program is executed
through the included Racket bridge. The private receipt stores both the full
emitted program's SHA-256 and each actual batched expression's SHA-256.

## Public and private evidence

Only `public/` is solver-visible. Each file contains demonstration input/output
pairs and query inputs, with no query answers, settings, seeds, reference code,
or rule hash. Filenames are `challenge-<24 hex digits>.json`, derived solely
from canonical JSON of the visible payload. Changing private metadata or any
query answer cannot change the public filename. Public directory names do not
encode a setting or setting-associated ordinal.

`private/manifest.json` retains the actual CLI invocation, seed, settings,
counts, source hashes, sampling receipts, and a map to public names. Private
episode files retain every answer, exact emitted Racket text/hash, all six
candidate programs and demonstration predictions, each query's rival evidence,
execution hashes, and the bridge/runtime identity. `private/rules/` contains
the six materialized exact programs named by their full SHA-256. Give a solver
the `public/` subtree only; the bundle root is an authoring artifact.

## Rejected controls and honest limits

Changing canvas size, object position, foreground palette, or sampling weights
alone is not a rule parameter. Background 7 and four-connectivity are fixed
object-role conventions here. Clockwise versus anticlockwise would produce
identical centered undirected lines, so it is rejected as an uninformative
parameter. Even lengths break the integer-center assumption. Bent or touching
components, mixed foreground colors, invalid ARC cells, unknown orientations,
and thresholds other than 3 or 5 are rejected rather than coerced. No API or
CLI control changes these constraints.

Deduplication has a finite total budget (`--max-attempts`, default 256). Exhaustion
raises `SamplingError` with requested/accepted counts, attempts, and rejection
counts. The CLI exits 2, emits a JSON failure receipt on stderr, and does not
return a shortened or cloned episode. Racket failures and ambiguous demos also
fail visibly; there is no Python fallback. A deliberately insufficient-budget
probe is:

```bash
python3 run_with_racket.py python3 generators/8b6a2892a064/workspace/parametric/prototype.py --seed 17 --demos 3 --queries 4 --max-attempts 1 --out ../checks/parametric/expected-bounded-failure
```

This command is expected to exit 2 before writing an output bundle. The receipt
should say one accepted input of seven requested after one attempt. Evidence
from one seed per setting is bounded; it does not prove all seeds, arbitrary
object layouts, output collisions, or all plausible alternative rules.

## Focused tests

From `WORK/`:

```bash
python3 run_with_racket.py python3 generators/8b6a2892a064/tests/test_parametric_prototype.py -v
```

These tests cover all six complete 3-demo/4-query episodes, distinct inputs,
demonstration-only filtering and per-query rival evidence, independent pair
counts, exact canonical Racket equivalence on the four public inputs,
out-of-bounds cropping, unchanged singletons, selective non-rotation, public
projection/name privacy, invalid controls/domain values, and bounded duplicate
sampling failure. Five contract tests can run without Racket by appending
`PrototypeContractTests -v` when invoking the test script directly. Racket
integration tests fail rather than skip if the included runtime is unavailable.

These are **prototype checks**. They do not replace canonical repair coverage
or independently approve the selected generator. The outer review records the
actual command outputs and retained evidence paths under `WORK/checks/parametric/`.
