# Port visibility threshold — proposed prototype

This task-local extension preserves the reasoning of `training:7df24a62`
(`c4f6a0585dbf`). It is **proposed**, outside the selected production generator
API, and is not variant approval or training admission.

## The one parameter

`min_visible_ports` is an exact integer in `{2, 3}`, fixed across every
training and query pair in an episode. **2 is the canonical/default rule.**
`materialize_program(2)` returns the canonical `program_solution` byte for byte;
3 changes its single `(>= (length placed4) 2)` comparison to 3. The canonical
program SHA-256 is
`34aea00434c1a498289ad35c068b9cca102078c262cc65b41c7b71871a563975`.
Source drift or ambiguous canonical programs fail explicitly.

For both settings the solver must find the color-1 source object's bounding box,
extract its color-4 ports and color-1 shape, consider all eight D4 transforms,
align **all in-bounds ports** to existing 4s, reject a candidate whose in-bounds
color-1 cells cover another color, and stamp only input zeros to 1. Candidates
may extend beyond the grid. Matching and obstruction checks read the original
input; stamping does not recursively trigger further matches.

The parameter changes whether a clipped candidate with only two visible ports
can stamp. It does not permit a missing *in-bounds* third port. An interior
three-port match stamps under both settings.

## Input and sampling contract

The sampler deliberately retains a useful subset of the canonical shape
family: 18–30 rows/columns, colors 0/1/4, one filled rectangle with three
interior port holes, source boxes 4×5, 5×4, or 5×5, and 17–47 total ports.
Outside port components are singletons or dominoes. Both settings use this same
three-port input constraint, so threshold 3 still teaches positive copies.
Every candidate is checked by the current selected generator's `self_check`.
No palette recoloring is used.

Each scene plants a full three-port copy and a lawful clipped two-port copy,
then scatters additional ports and applies a whole-scene D4 transform. A scene
is retained only if the two rules actually disagree and the full copy changes
at least one zero under threshold 3. This checks observable effects even if
extra accidental matches occur. Positions, dimensions, port arrangements,
transforms, and distractors vary. These are constructed teaching scenes, not
claims about the distribution of ordinary production draws.

`generate_episode(seed=..., min_visible_ports=..., n_train=..., n_test=...)`
accepts 1–16 demonstrations and independently 1–16 queries. The default is 2
and 4. One demonstration suffices within the declared two-rule family because
every scene contains a threshold witness. If the parameter is omitted, one
setting is selected once from the seed by a separate deterministic random
stream. Explicit settings use the same seed-based scene stream, allowing a
paired comparison. Seeds must be exact integers in 0 through `2**64 - 1`;
bools, floats, and numeric strings are rejected by the Python API.

There are at most `max_attempts` scene draws per episode: default 128, allowed
1–4096. The scatter pass itself visits at most all grid cells once. Duplicate
inputs or failed structural/observable-witness checks consume attempts.
Insufficient accepted inputs raises `SamplingExhausted` with the requested and
accepted counts and rejection reasons; no partial episode is returned.
Demonstrations and queries are pairwise distinct. Counts at the upper limits
are supported API bounds, not an all-seed success claim.

## Execution and certificates

The Python mirror is used only for bounded candidate screening. Every accepted
input is then executed under **both exact Racket programs**, through the
included protected `RacketBridge`. Only the outer `rule!` command wrapper is
removed to apply its unchanged lambda, as in the executor interface. A mirror
mismatch aborts generation. Racket results are cached by exact input hash and
threshold within the process; cached labels were originally executed by Racket.

The certificate first compares each setting's executed predictions against
**demonstration outputs only**. It records which demonstrations reject each
setting. It then evaluates each distinct query input, records both prediction
hashes and their disagreement count, and checks agreement among the
surviving settings. The certificate never reads query answers or private seed
or parameter fields. Generation requires the intended setting to be the sole
survivor. This establishes identifiability only within `{2, 3}`; it does not
establish universal rule uniqueness or eliminate unrelated shortcuts.

Private episodes retain the full selected labels, both settings' Racket
outputs, threshold/full-copy witness coordinates, rejection counts, programs,
source hashes, and certificates. Each program is also materialized as a `.rkt`
file. Source hashes cover this prototype, the exact selected generator used
for checks, the shared public projection helper, Racket bridge, and prelude.

## Exact four-query command

From the packet's `WORK/` directory, with the supplied runtime configured:

```bash
python3 run_with_racket.py python3 \
  generators/c4f6a0585dbf/workspace/parametric/port_threshold.py \
  --seed 17 --settings 2 3 --train 2 --test 4 --max-attempts 128 \
  --out ../checks/parametric/batch
```

The wrapper runs its payload from `WORK/repo/`, so that output path is
`WORK/checks/parametric/batch`. The destination must not exist. This writes one
complete episode per setting, with four queries each. In an ordinary checkout,
run the payload directly from the repository root, with Racket on `PATH` or
`RACKET_PATH` set, and choose a new output directory.

The verification command from `WORK/` is:

```bash
python3 run_with_racket.py python3 \
  generators/c4f6a0585dbf/tests/test_parametric_port_threshold.py
```

It uses Python's standard-library `unittest`; no pytest installation is needed.
The existing runtime dependencies (including NumPy and Pillow) and actual
Racket are required. Missing Racket is a test failure, not a skipped pass.

## Public/private export boundary

Give a solver **only `batch/public/`**. Every public file contains exactly
`train` with inputs/outputs and `test` with inputs only. Both its canonical
bytes and its full SHA-256 filename come from the shared
`reviewer_support.public_challenge_bytes` / `public_challenge_id` helpers.
Public filenames contain no seed, threshold, or setting-associated ordinal;
batch ordering is sorted by these visible-content IDs. Private metadata or
query-answer changes cannot change an ID. Duplicate visible payloads are
rejected before any output directory is created.

`batch/private/` contains full episodes, labels, parameters, seeds, programs,
source hashes, and the execution/export receipt. It is authoring evidence and
must stay separate from public challenges. The writer validates exact program
hashes and their correspondence to the declared setting. The caller chooses
the destination; use a neutral directory name rather than embedding a hidden
setting or seed in a public path.

## Focused verification and remaining limits

The task-local tests cover invalid numeric types/bounds; canonical byte
identity; all 10 supplied labeled canonical pairs; executed Racket/mirror
parity; reproducibility; independent pair counts; four distinct queries;
threshold witnesses and nonidentity stamps; demonstration-only certificates;
explicit ambiguity; bounded duplicate retries; opaque sorted public exports;
private program materialization; duplicate-visible rejection; and held-out
answer/metadata invariance.

The retained export and test run are bounded evidence. They do not certify all
seeds, maximum counts, or every lawful canonical input. The scene layout is
purposefully restricted and rejects cases where other matches mask the
threshold distinction. No production API, canonical authority, shared runtime,
approval identity, or training policy is changed by this prototype.
