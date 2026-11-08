# Proposed alternating-tile parameter prototype

**Status: PROPOSED prototype.** This task-local tool generalizes only the starting
phase and repetition count of task `75ba893e1e36` (original ARC `59341089`). It does
not change the selected generator, canonical rule, catalog kind, approval hashes,
or shared runtime API. Canonical repair coverage is reported separately.

## Bounded rule and episode contract

| Parameter | Allowed values | Original/default |
|---|---|---|
| `first_tile` | `mirror`, `input` | `mirror` |
| `tile_pairs` | `1`, `2`, `3` | `2` |

Every output alternates the horizontal mirror of the input and the input itself,
starting with `first_tile`, for `tile_pairs` complete two-tile pairs. The six
settings execute six distinct Racket programs. The original setting emits the
canonical authority's exact bytes:

```racket
(rule! (lambda (g) (stack-grids 'horizontal (list (flip-lr g) g (flip-lr g) g))))
```

`choose_parameters(seed)` chooses both values once by indexing the ordered six
settings with `seed % 6`. Settings are ordered mirror/1, mirror/2, mirror/3,
input/1, input/2, input/3. Seed 1 therefore selects the original setting.
A complete episode always contains three demonstrations and one query under the
same emitted program. The seed is private authoring metadata.

Inputs are exactly 3x3, use colors drawn from 5, 7, and 8, and contain at least
one row whose left and right cells differ. Generated teaching witnesses use all
three colors; canonical inputs may use a subset. Four locally authored witness grids are
permuted deterministically by color and row using `seed // 6`; they do not import
or draw from the production generator. The six seeds in a comparison block share
the same inputs, so the rule change is directly observable. Output widths are
6, 12, or 18, all within the maximum side length of 30.

The asymmetry constraint is necessary to distinguish the two first-tile choices
when their repetition counts are equal. Different counts are already visible in
output width. Every retained demonstration is checked against each of the five
other declared settings before the query's distinction is used.

## Exact runnable commands

Run these from the outer extracted packet directory containing `review.py`:

```bash
python3 review.py run python3 generators/75ba893e1e36/workspace/parametric/probe.py --seed-start 0 --out ../checks/parametric/bounded-six-v2
python3 review.py run python3 generators/75ba893e1e36/tests/test_parametric_prototype.py
```

The evidence directory must be new. Use a different `--out` path for another run;
the probe deliberately refuses to overwrite prior evidence. `--seed-start` selects
six consecutive deterministic seeds and thus covers every allowed setting. This
is an authoring probe, not a blind solve or a production dataset export.

The wrapper selects the included offline Racket and runs payloads from `WORK/repo`.
In a normal relocated repository with its declared dependencies available, the
same payloads can run from the repository root with `PYTHONPATH=src:shared/runtime`
and `RACKET_PATH` set to its local executable. There are no sibling-checkout
imports or absolute source paths in the tool or tests.

## Exact execution and retained evidence

`prototype.py` exposes deterministic inputs, parameter selection, program
construction, Racket-backed episode construction, and public redaction.
`probe.py` materializes all six programs and episodes and checks their rivals.
There is no Python implementation that supplies or substitutes for output labels.

The included `RacketBridge` receives the exact emitted program inside:

```racket
(let ((rule! (lambda (f) f))) (<exact-emitted-program> '<input-grid>))
```

The six emitted programs all pass a closed lambda to the REPL registration form
`rule!`. The local lexical identity binding returns that exact lambda for native
Racket application. It does not parse, rewrite, or substitute the program body.
The adapter deliberately supports only these six known closed-lambda programs;
it is not a proposed replacement for the production executor.

Evidence is retained under `WORK/checks/parametric/bounded-six-v2/`:

| File | Contents and intended visibility |
|---|---|
| `report.json` | **Private authoring evidence:** seeds, parameters, source/program hashes, actual commands, canonical comparisons, rival identifiability, witness and limitations |
| `executions.jsonl` | **Private authoring evidence:** every actual Racket expression, output or error, context, hash and elapsed time |
| `private/programs/program-00.rkt` through `program-05.rkt` | Exact executed rule text, with no added newline; hashes bind the saved bytes |
| `private/episode-00.json` through `episode-05.json` | Complete episodes with seed, parameters, program and query answers |
| `public/episode-00.json` through `episode-05.json` | Only `train` input/output pairs and `test` inputs; no seed, parameters, programs or query answers |

Only the six `public/` JSON files are model-visible challenges. All other files
contain authoring-only information. Public filenames are neutral episode indexes,
and no mapping file is placed in `public/`.

A complete successful bounded run records 24 selected labels, 120 alternative
rule predictions, and 10 canonical executions (canonical and prototype-default
execution for each of five labeled pairs): 154 grid applications in total.
The report checks six complete episodes, 30 directed parameter rivals, and one
lawful input with six distinct executed outputs. The original is required to be
byte-identical to the canonical ledger program and agree with all five canonical
labeled pairs. The standalone five-test unittest module uses `reviewer_support` public
helpers and resolves data relative to its own tree. When Racket is unavailable,
its runtime-dependent tests explicitly skip; the packet command supplies Racket.

The runner writes an initial report and flushes every execution record. Failures
are retained with their exception and partial artifacts, and cause a nonzero exit.
Source hashes cover both Python tools, this README, and the focused test. Artifact
hashes cover the public/private files and execution trace; the report cannot hash
itself, so external receipt or return-manifest hashes bind its final bytes.

## Limits

This is bounded evidence for six settings and six seeds, with a deliberately small
set of teaching inputs. It does not establish diversity or universal lesson
identifiability, and it tests only the other declared parameter settings as
rivals. Palindromic teaching grids are excluded because their first-tile phase is
unobservable. Arbitrary input sizes, palettes, unrelated rule mutations and
production parametric integration remain outside this prototype. Acceptance of
the separately repaired canonical generator does not approve these variants.

## Retained first-attempt failures

`WORK/checks/parametric/bounded-six/report.json` and its `executions.jsonl` retain
the first failed run: 150 actual Racket applications, six identified episodes,
then a validator error on canonical train[3], whose palette is {5, 7}. Exact
first-attempt source snapshots and their receipt are in that run's `failed-source/`
and `failure-source-receipt.json`. The validator was corrected to admit subsets of
the allowed palette; witness sampling still uses all three colors. The focused
before-fix reproduction is `WORK/checks/parametric/palette-regression-before.log`.

The original pytest invocation failed because the selected Python had no pytest;
`WORK/checks/parametric/prototype-tests.log` retains that environment failure.
The final focused tests use standard-library unittest and need no package install.
The successful rerun, if its report says `passed`, is `bounded-six-v2/`; the failed
report is not rewritten or relabeled as success.
