# Opt-in parametric proposal: guide/crop tie policy

This workspace prototype extends generator **4512012999bb**, whose parent is
**training:846bdb03**. It does not edit or select `../../generator.py`. The
canonical task and its rule remain the reference. This is an independently
replayable proposal; it does not assert completion of the normal review intake.

## Run

From the outer review packet directory, use its existing `review.py run` entry
point. That command runs its payload with `WORK/repo` as the working directory
and provides the repository's Racket runtime and Python import paths.

```bash
python3 review.py run python3 -B generators/4512012999bb/workspace/parametric/prototype.py --seed 17 --setting all --train 3 --test 4 --out ../checks/parametric/final
```

For one episode, choose `--setting direct` or `--setting mirror`. Omitting
`--setting` selects the canonical **direct** tie policy. `--train` and `--test`
are independent; their defaults are 3 and 4. The supported ranges are 3–64 demos
and 1–64 queries. Three demos are required to teach a positive-score tie, a
strict direct decision, and a strict mirror decision. Each split/index has an
independent deterministic random stream. No global random state is used.

Choose a **new** `--out` directory every time. Existing destinations are refused.
`--max-attempts` bounds construction attempts per scene (default 64; maximum
256). A failure reports the scene and bound. `--timeout` bounds each Racket
evaluation (default 30 seconds). `--canonical PATH` can explicitly identify a
canonical JSON or JSONL file; it is unnecessary in the complete review runtime.
The raw canonical program hash is checked before generation.

## Semantic parameter

`tie_policy` takes the values **direct** and **mirror**. The CLI calls this
choice `--setting` and also accepts `all` to emit one episode of each setting.
Every program retains the same backbone:

1. Search for two nonzero vertical guide segments with equal endpoint colors.
2. Find the bounding box of all remaining nonzero cells; it must be two rows
   and two columns smaller than the guide-defined frame.
3. Score the detached crop in both horizontal orientations using the **first
   interior** color of each guide. An odd center column contributes to neither
   score; non-side colors also contribute to neither score.
4. Copy both guide columns row by row into the output, leave the top/bottom
   interior zero, and insert the chosen crop orientation.

The `direct` materialized program is byte-for-byte the exact canonical
`program_solution`. Its raw SHA-256 is:

```text
e3238cefdd981958e0835cc7d91d0680cd68f3d3db6321936805ae88fb3f1beb
```

The `mirror` program changes exactly the sole comparison
`(> (score #t) (score #f))` to `(>= (score #t) (score #f))`.
Construction fails if that exact selector is missing or occurs more than once.
Two teaching rivals, `always-direct` and `always-mirror`, replace only that same
selector with `#f` or `#t`. They are declared diagnostic rivals, not settings
that the generator selects.

Every label and every rival prediction comes from the actual **RacketBridge**.
The original wrapper and complete program source are evaluated unchanged under
a lexical identity binding for `rule!`. Python samples inputs and checks shape,
guide, crop, score, and serialization invariants; it is not the label backend.
Generation first replays all five labeled original pairs with the exact
canonical program. The original examples alone do not demonstrate tie policy.

## Teaching and queries

The first three demos contain an asymmetric **positive-score tie**, a strict
direct case, and a strict mirror case. Different top-corner accents make every
crop visibly different from its horizontal reflection. All scenes must have
exactly one canonical guide/crop candidate. All inputs are distinct across
demos, queries, and both settings in an `all` batch.

The four default queries use crop sizes **7×7, 8×8, 8×9, and 10×10**; the three
default demos use **3×4, 3×6, and 4×6**. Query decisions are respectively tie,
strict direct, strict mirror, and tie. Query crops mix correct and opposite side
colors; their strict score margins are two cells. Queries also vary guide-wall
colors after the first interior row, preserve accent colors, and include odd
widths whose colored center column must be excluded from scoring. Larger active
crops increase the cells that must be counted and copied. Surrounding blank
padding is placement variation and is not claimed to add reasoning difficulty.

## Public/private boundary and identifiability

`public/` contains only `<visible-content-sha256>.json` files. Each file is
written using the repository's `reviewer_support.public_challenge_bytes`, and
its name comes from `public_challenge_id`. The only visible fields are demo
inputs/outputs and query inputs. Identity is the hash of those exact bytes,
including the helper's trailing newline. Public names contain no setting,
seed, program, task, or answer metadata. Batch order is the sorted content-ID
order recorded privately.

`private/manifest.json` contains the selected setting, scene facts, hidden query
answers, the complete four-program prediction matrix, provenance hashes, and a
certificate for **each query**. `private/programs/` contains the exact four
materialized Racket programs and their hashes are recorded in the manifest.
Share only the `public/` files for a blind challenge.

The certificate first eliminates declared programs using **only demo outputs**.
It then groups the survivors' predictions for each query. A query is identified
when every surviving declared program predicts the same output. Generation
requires the selected policy to be the sole surviving program, and requires
every query to be identified. This establishes identifiability only within the
four explicitly declared programs. It makes no claim about all possible ARC
rules, unseen shortcut hypotheses, or a learner's empirical solve rate.

## Verify

Source-only contract tests need only the Python standard library:

```bash
python3 review.py run python3 -B -m unittest discover -s generators/4512012999bb/tests -p test_parametric_4512012999bb.py -v
```

Replay the generated batch using actual Racket again, checking materialized
program bytes, source hashes, public hashes, all predictions, private answers,
and the demo-only certificates:

```bash
python3 review.py run python3 -B generators/4512012999bb/workspace/parametric/evidence.py --batch ../checks/parametric/final --out ../checks/parametric/final/private/evidence.json
```

The evidence script bounds replay to 64 generated scenes by default (adjustable
up to 256). For the two default episodes it replays 14 generated scenes against
four programs plus the five canonical examples: **61 Racket evaluations**. It
refuses replay if the proposal source, canonical source file, or selected
generator has changed since generation. The resulting private report binds the
observations to the source, materialized programs, manifest, executable,
prelude, and bridge hashes. This is an authoring audit, not a blind solve.
