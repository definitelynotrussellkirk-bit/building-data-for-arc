# Transparent-object beam prototype

**Status: proposed, task-local prototype.** This extends original training
family `6ffe8f07 / 0b8ba9bb3c63`. It does not select a new production rule,
change the canonical generator, or grant approval or training admission.

## One bounded rule parameter

| Parameter | Allowed values | Original/default | Executed effect |
|---|---|---|---|
| `transparent_color` | `2` (red), `3` (green) | `2` | Rectangles of this color let the beam pass and are overwritten only where the cross reaches them. Other non-cyan colors clip their individual rays and are restored. |

The cyan rectangle remains the emitter and the yellow cross spans its complete
row and column bands. Clipping is calculated separately for every beam row or
column; nearer blockers take precedence where blockers share a ray. The
transformation retains opaque objects and parts of transparent objects outside
the reached cross. These reasoning steps are invariant across both settings.

The parameter changes a role in the rule, rather than recoloring an output.
Both red and green rectangles occur on the same input and intercept different
beam rays. A paired seed therefore retains **identical input geometry and
colors** while changing which rectangles block or transmit the beam.

`canonical_rule.rkt` is the exact original `racket_target.raw_code` snapshot;
`canonical_source.json` records its authority and hashes. Setting `2` returns
those bytes without a change. Setting `3` changes the single transparent-color
predicate. The normalized canonical SHA-256 remains
`757441c9ab4aa17070a3826de76e0b0f74e66636398f3f3aaa4392e47af17bcb`.
The tests independently load and execute the canonical authority and compare
all six unique official inputs against their supplied outputs.

## Run four-query episodes

From the packet's `WORK/` directory, after installing this workspace under its
assigned generator, run the original setting:

```bash
python3 run_with_racket.py python3 generators/0b8ba9bb3c63/workspace/parametric/prototype.py --seed 17 --transparent-color 2 --demos 3 --queries 4 --out ../checks/parametric/red-17
```

Run the alternative on the same input draws:

```bash
python3 run_with_racket.py python3 generators/0b8ba9bb3c63/workspace/parametric/prototype.py --seed 17 --transparent-color 3 --demos 3 --queries 4 --out ../checks/parametric/green-17
```

Demonstration and query counts are separate. For a boundary-size episode:

```bash
python3 run_with_racket.py python3 generators/0b8ba9bb3c63/workspace/parametric/prototype.py --seed 29 --transparent-color 3 --demos 5 --queries 4 --height 30 --width 30 --out ../checks/parametric/green-29-30x30
```

`--transparent-color sampled` chooses one of the two settings deterministically
from the episode seed, once for the entire episode. Omitting that option uses
canonical setting `2`. Input layout draws use a separate seed stream and do
not depend on the chosen setting. `--demos` and `--queries` each accept integers
from 1 to 32. `--max-attempts` bounds sampling, defaults to 256, and accepts
1 to 10,000. The seed accepts signed 64-bit integers.

Output directories must be new; an existing directory is not overwritten.
Every accepted input is distinct from all other demonstrations and queries in
the same episode. An exhausted sample budget raises an error instead of
cloning inputs or returning a short episode.

## Execution and evidence

All labels, including all four query targets, execute the materialized Racket
program using the packet's protected `RacketBridge` and shared `wrap_rule`
normalization. There is no Python label mirror or fallback. The packet wrapper
selects the included offline Racket runtime. In source checkouts the prototype
maps the `scripts` namespace to `shared/tools` next to that **same imported
runtime**, because the shared normalizer imports `scripts.comment_solutions`.
Portable copied runtimes already provide `scripts/` and need no mapping.
This adapter changes no shared file and introduces no sibling-checkout import.

Each run writes:

| File | Audience and content |
|---|---|
| `challenge.json` | Public: only demonstration input/output pairs and query inputs. No parameters, seed, rule, metadata, or query answers. |
| `episode.private.json` | Authoring: fixed parameter, seed, accepted draw indices, every Racket label, exact rule and rival text, source hashes, runtime identity, limitations. |
| `rule.rkt` | Exact Racket rule used for every pair in this episode. |
| `rivals/*.rkt` | Exact executable sources of the finite declared rival family. |
| `identifiability.json` | Demonstration-only eliminations and a separate prediction-agreement check for every query. |
| `manifest.json` | Actual invocation, authored source hashes, counts, and SHA-256 hashes of all other files in this run. |

Give a solver only `challenge.json`. The directory's other files are private
authoring evidence. A parameter is intentionally inferred from demonstrations;
it is not encoded in the query input or a public metadata field.

## Declared-rival identifiability

The seven Racket programs are:

1. Red-transparent setting.
2. Green-transparent setting.
3. All non-cyan rectangles opaque.
4. Both red and green transparent.
5. Ignore clipping but restore opaque rectangles after painting.
6. Use one clipping limit for an entire arm instead of separate row/column rays.
7. Let the chosen color transmit the beam, but restore its original paint.

For each rival, the first inconsistent demonstration is retained with its index,
changed-cell count, and prediction hash. Only rivals agreeing with **all**
demonstrations survive. For each query input, the surviving rules are executed
and their predictions must agree. The certification function accepts query
inputs alone; it has no query-answer argument and never learns from another
query's answer. The intended setting must also survive its own demonstrations.
Insufficient teaching evidence fails the episode explicitly.

The constructive inputs show partial clipping, opaque material behind a stop,
overlapping near/far blockers, transparent objects extending outside beam bands,
and separate off-band objects. One such demonstration distinguishes this finite
rival set, while the default three demonstrations vary emitter size, position,
blocker coverage, orientation, and candidate-color placement. This is a bounded
identifiability check, not uniqueness among all conceivable rules.

## Input constraints and limitations

The sampler supports exact height and width values independently in **17..30**.
Without overrides, it samples each side in that range. The lower bound leaves
room for separated candidate-role objects, partial near/far blockers, and
observable space behind the far blocker; it is a prototype construction limit,
not a change to the canonical generator's 11..30 contract. Every source object
is a solid rectangle, there is one cyan emitter, black is the unique modal
background, and no input cell is yellow. Both candidate transparent colors and
blue opaque blockers are always present. The same input constraints hold for
both parameter settings.

The input grammar is deliberately bounded and more structured than the full
canonical generator. Rectangular scenes use horizontal/vertical reflections;
square scenes may additionally transpose. No corpus-wide difficulty, complete
rule-identification, or arbitrary-seed performance claim follows from these
tests. A 30×30 run exercises longer actual beam paths and the same clipping
roles; it is not just padding a fixed smaller scene.

## Focused prototype tests

From `WORK/` after installing the task-local files:

```bash
python3 run_with_racket.py python3 -m unittest discover -s generators/0b8ba9bb3c63/tests -p test_parametric.py -v
```

The tests cover the exact default source and all six canonical inputs;
hand-checked transparent-fragment, nearest-stop, and per-ray behavior; two
fixed-setting episodes with four queries each; deterministic seed selection;
independent counts; the 17×17, 17×30, 30×17, and 30×30 sampler boundaries;
demo-only rival checks and a deliberately ambiguous no-demo control; public
field whitelisting; exact evidence hashes and non-overwrite behavior; invalid
parameters, dimensions and grids; budget exhaustion; and a runnable CLI.

This coverage is **prototype scope**. Canonical generator repair checks and
production four-query checks are retained separately by the reviewer.
