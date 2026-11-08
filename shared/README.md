# Shared helpers and tools

`runtime/puzzle_generators/base.py` and `runtime/puzzle_generators/helpers/`
provide the existing deterministic context and grid, placement, palette, object,
shape, and self-check helpers. `runtime/arc_repl/` contains the Racket bridge and
prelude. The required data/loading primitives are under `runtime/src/core/`.

`tools/` contains the inherited linter and review-tool implementations, with
maintained fixes tracked in Git. The supported public entry points
are `arcpuzzles tools`, `arcpuzzles check ID --stage STAGE`, and
`arcpuzzles review pick`; do not invoke a tool directly from this storage layout.
The public commands prepare the complete ordinary execution layout the tools
expect, entirely from this repository.

| Stage | Purpose |
|---|---|
| `lint` | Generator metadata, API shape, axes, RNG, and bounded validation |
| `selfcheck` | Determinism, self-checks, and mutation sensitivity |
| `rule_smoke` | Real Racket execution, output diversity, purity, and restarts |
| `defect_lint` | Known defect patterns and stale rule pins |
| `dist_gate` | Generated/canonical distribution comparison |
| `profile_floor` | Canonical acceptance and exact-profile support |
| `semantic_gate` | Semantic witnesses, lessons, and counterfactual contracts |
| `diversity` | Input and output diversity |
| `override` | Override contract, axis coverage, and unknown-key behavior |
| `grammar` | Canonical DSL grammar and callable coverage |
| `racket_lint` | Canonical Racket source lint |
| `authority_sync` | Selected versus archived rule authority agreement |

The original battery owns the stage arguments and advisory distinctions.
`arcpuzzles check` runs a before/baseline stage, retaining nonblocking advisories
as such. A zero process exit with an advisory is not a semantic PASS. The
recorded battery summary distinguishes these outcomes. Use the after phase in a
review workspace for the stricter post-change policy.
After-repair semantic checks now include a query-rotation smoke test on their
existing labelled lessons. Its separate diagnostic verdict does not reject an
intentionally ordered production curriculum. To require rotation-safe lessons,
use `arcpuzzles check ID --stage semantic_gate --require-rotations-identifiable`
(or add the flag to `--battery`). It fails on rotation ambiguity, hook warnings,
scoring/materialization errors, and a missing lesson contract. The retained
settings and native checkpoint subject bind this policy; repeat the flag on
`--resume` (and native `--status`). Diagnostic checkpoints cannot stand in for
a required-rotation run. This smoke test
does not replace a larger census or exhaustive cyclic-window probe.

For smaller override receipts, use `arcpuzzles check ID --stage override
--compact-results --out var/checks/ID-override` or add `--compact-results` to
`--battery`. Only successful per-case detail is omitted. Totals, every failed
case row, every structured finding, the full case matrix, source/checker hashes,
replay settings and a digest of the complete case rows are retained. Console
witness limits do not truncate failure evidence. A large failure set may still
produce a large receipt. Repeat the same flag on public `--resume` and native
battery `--resume`/`--status`; changing it selects a different evidence subject.
Public checkpoints predating this explicit setting are refused; keep their
evidence and choose a fresh `--out` for the current tools.
Compact receipts do not change draws, gate verdicts or approval.

Output diversity and solid-output diagnostics name the existing generator
contracts. `EXPECTED_OUTPUT_CODOMAIN` must be justified from the selected
canonical rule, and the probe must cover the declared alphabet; a collapsed
sample cannot justify a smaller declaration. `SOLID_OUTPUT_JUSTIFICATION`
needs a concrete explanation of at least 30 characters and a `self_check`;
verify lawful endpoints against source-bound canonical-rule examples. These
declarations keep their existing checks and do not certify teachability.

`tests/` retains common regression tests. Generator-specific tests are stored
with their generator. `data/` retains canonical puzzles, rule authority files,
and approval/review ledgers; these are data, not generated model context.

Temporary runtime copies are disposable. Change shared source here, then prepare
a fresh runtime when verifying a change. Never edit the predecessor repository
to repair a missing dependency in this one.

## Visible grid inspection (safe during a solve)

Solve preparation automatically labels every visible example before its arrays:
`Input: H rows × W columns. Output: H rows × W columns.` Query outputs always say
`Output: unknown`. The solve README repeats this view of the unchanged public
`challenge.json`; it contains no private query dimensions or labels.

```bash
arcpuzzles grid challenge.json
arcpuzzles grid challenge.json --json
arcpuzzles grid expected.json --compare actual.json
```

From an extracted packet root, use
`PYTHONPATH=repo/src python3 -m arcpuzzles grid solve-blind/challenge.json`
(or `solve/challenge.json`). No Racket setup or catalog lookup is needed.
The API is `from arcpuzzles.grids import inspect_grid, inspect_task, compare_grids, format_task`.
It accepts JSON-style integer grids. Inspection reports height, rectangular width
(or `null` with ragged row lengths), colors/counts and zero-based (row, column)
coordinates from the top-left. Empty/ragged grids remain inspectable; malformed
rows/colors raise an actionable error. Task inspection accesses train inputs and
outputs and test inputs only, even if the file also contains test outputs.

Comparison aligns the same coordinates without resizing or inferring shifts.
It reports changed cells, missing/extra rows, missing/extra columns per shared
row, and all missing/extra cells. Shapes need not match to compare safely.
This is a diagnostic: exit 0 means inspection completed; read `equal` in a
comparison report to determine equality. These commands do not alter files,
certify a generator, or add an intake gate.

## Opt-in reviewer lesson census

```bash
PYTHONPATH=src python3 -m arcpuzzles lesson-census ebff81ea3252 \
  --per-band 20 --train 3 --test 1 --period 6 --out var/lesson-census.json
```

This public command replaces task-local lesson probes. It snapshots the selected
library, runs `runner.run_one` with the selected Racket authority, and dynamically
reads `LESSON_COMPETITORS`, `SEMANTIC_RIVALS`, and `CANONICAL_SHORTCUTS`.
Declarations retain their namespaces, even when names collide. Each report
contains the full copied-source manifest, generator/rule hashes, replay seeds,
exact instances and their hashes, per-band rival counts, requested cyclic-start
coverage, and exact unique-input counts. Consecutive lesson starts avoid stride
aliasing; `--period` is the reviewer's reporting modulus. The materializer can
reject inputs and advance indices, so requested start coverage does not claim
accepted-pair residue coverage. Actual accepted train/test residues are now
reported separately in `per_band.accepted_pair_residues`, with the number of
recorded indices. Each new per-puzzle instance carries `sampling.accepted_pairs`
with split, pair position, actual sample index and full input SHA-256, plus the
requested start, attempt count, next index and rejection reasons. Both the public
materializer and census runner record indices where the draws are accepted;
legacy missing metadata is not reconstructed by assumption.
The command does not rotate a materialized
instance unless requested. Add `--rotate-query` (requires `--test 1`) to hold out
each of its labelled pairs once, using the other pairs as demonstrations in
their original order. No new Racket labels or generated pairs are needed.
Declared rivals must be pure and deterministic: predictions are cached by rival
name/input hash. The report retains every rotation's query index, demonstration
indices, rival statuses, warnings and errors next to the original instance hash.
Rotations include the original query position; they are not independent draws
or exhaustive coverage of all cyclic windows. The report has separate
`production_status` and `rotation_status` values. By default, measured rotation
ambiguity contributes to the overall status (`--rotation-policy require`). For
an ordered production curriculum, add `--rotation-policy diagnostic`; rotations
remain recorded, but only production findings determine the overall verdict.
Neither policy makes a finite rival test proof of identifiability.
Every difficulty is passed explicitly; unsupported
generation arguments produce errors rather than silently changing the population.
`--train` defaults to `EXAMPLES_NEEDED` (or 3 if absent).

A rival fitting all demonstrations **and disagreeing on any query** is measured
ambiguity. A rival agreeing everywhere is `survived_all`, not an ambiguous query.
The top-level `summary` distinguishes production `ambiguous` lessons from
`ambiguous_rotations`, and separates materialization/scoring errors and hook
warnings. `no_ambiguity_found` means no ambiguity against the declared rivals in
the sampled lessons/rotations; older reports used `no_declared_ambiguity`.
The `lesson_identifiable` hook's reasons are separate warnings. Missing contracts,
invalid declarations, execution failures and timeouts remain explicit. Exit codes:
0 for completed evidence without a measured ambiguity/error (including warnings,
`hook_only`, and `no_contract`); 1 for measured ambiguity; 2 for errors. Inspect
`status`, not just the exit code. This is finite evidence against declared rivals;
it neither proves identifiability nor changes approval. Only per-puzzle generators
are currently supported. Every completed lesson flushes and fsyncs a checkpoint
before replacing the prior report. Runtime
failures and hard timeouts retain the latest partial report and logs as errors.
Canonical rival-fit metadata separately records which declarations fit every
labeled canonical pair, which are refuted, and which failed to execute. Unlabeled
test queries are excluded from this comparison; malformed present labels and
an empty labeled set are errors.

In an extracted packet, run the same command through `run_with_racket.py` with
`python3 -m arcpuzzles lesson-census ...` as its command. It is an optional reviewer
tool, not another routine intake gate or a new battery stage.

### Enumerate a declared finite schedule

A generator can declare `LESSON_SCHEDULE_PERIOD = P`, a positive integer
asserting that its semantic sample-index schedule repeats modulo P for every
requested difficulty. The tool does not infer P from `--period`, profile lists,
or observed grids, and does not prove the declaration. Missing, boolean, or
nonpositive declarations are errors in enumeration mode.

```bash
arcpuzzles lesson-census TASK_ID --enumerate-schedule-period --schedule-seed 0 \
  --band easy --band medium --band hard --out var/schedule-census.json
```

This opt-in mode overrides `--per-band` with P, invokes the production
`runner.run_one` at every consecutive start 0 through P−1 for each requested
band, and holds out every materialized labelled pair once. It requires one query
and uses the same explicit seed at every start and band (`--schedule-seed`,
default 0). The normal sampler, rejection handling and Racket reference labels
remain in force. Accepted pairs may skip rejected or duplicate indices; their
actual indices and rejection receipts remain attached to each instance.
`--period` still only controls residue reporting tables.

The source-bound `schedule_coverage` receipt records the declared period, fixed
seed, bands, expected lesson/rotation counts, and generator/rule hashes.
`complete_fixed_seed` means all these starts and query positions were materialized
and scored at that seed. It is coverage, not a passing semantic verdict; inspect
`production_status`, `rotation_status`, and `status` for findings. It does not
exhaust random support, all possible accepted-pair schedules, or undeclared
schedules. Checkpoints and failed or partial runs retain `incomplete` coverage.
For an explicitly ordered curriculum, `--rotation-policy diagnostic` preserves
rotation findings while keeping their semantic verdict out of the overall
verdict; incomplete enumeration remains an error with either policy. Reports
contain private reference labels and must stay in authoring/evidence storage.
Ordinary census defaults are unchanged. Enumeration cannot be combined with
`--rescore`; rescoring saved schedule evidence checks its retained coverage and
source bindings but cannot establish the current generator's schedule.

To consume a completed, successful receipt in the semantic gate, use
`arcpuzzles check TASK --stage semantic_gate --schedule-census FILE --schedule-seed 0`
(also supported by the battery and audit preset). This requires current source,
rival inventory, period, seed, all three bands and every required query rotation
to match. Accepted status is `complete_fixed_seed_reported`; rejected inputs and
their hashes stay in the check evidence. See the
[receipt contract](../docs/SEMANTIC_GATE_CONTRACT.md#consuming-a-fixed-seed-schedule-census)
for exact checks, resume binding and limits.

### Recheck saved lessons after changing rivals

```bash
arcpuzzles lesson-census TASK_ID --rescore var/lesson-census.json \
  --out var/lesson-rescore.json
```

This optional mode reuses a complete `arcpuzzles-lesson-census-v1` report and
checks **every** single-pair query holdout with the current declared rivals.
It calls the same scorer and rotation code as a fresh census. It generates no
new inputs and executes no Racket labels. Sampling flags describe fresh censuses;
rescoring uses the saved population and always requires rotations in its verdict.
Use a new output path. The report binds `input_census_sha256` and
`input_generator_sha256` separately from `rival_generator_sha256` and the current
runtime manifest. Changed rule bytes, incomplete/error evidence, bad retained
hashes, duplicate lesson identities, or malformed labelled grids reject rescoring.
These checks verify internal bindings; they do not independently certify labels.

`rival_summary` keeps production and rotation status counts for each namespaced
rival, plus its first exact ambiguity counterexample: original instance and hash,
seed/index, query position, demonstration positions, and rival prediction.
Detailed lesson scores and errors remain in the report. An answer-equivalent
rival is `survived_all`; it is not an ambiguity. A zero verdict concerns only
these saved lessons and the declared rivals, and cannot establish universal
identifiability or improvement in newly generated lessons. Rescoring does not
change approval or add a maintainer intake step.

## Portable canonical test data

Copied runtimes now expose `reviewer_support.py` at their root:

```python
from reviewer_support import canonical_pairs, find_root

pairs = canonical_pairs("ebff81ea3252", root=find_root(__file__))
```

Run task tests from the runtime root with `python3 -m pytest tests/TASK_ID`.
`find_root` also recognizes a library's `shared/data` layout. `canonical_pairs`
uses exact IDs, reads all canonical variants by default (`variant=0` selects one),
normalizes row strings and singleton splits, and preserves variant/split/pair
indexes. Missing tasks and malformed pairs raise visibly. This is authoring data
with answers: do not load it during a blind solve. The source implementation lives
at `shared/runtime/reviewer_support.py`; no sibling checkout is needed.
The optional `labeled_only=True` skips only test pairs without an `output` key;
it still validates their inputs and rejects missing train labels or malformed
present outputs. The default requires labels on every pair.

For a portable task-local test, use `find_root(__file__)` rather than the current
working directory. Run it through the packet wrapper, or use
`arcpuzzles check TASK --stage task_tests` for a retained legacy test that imports
`scripts.*`. That namespace exists in the staged runtime, not the library's
direct pytest layout. The staged command preflights tests without importing them. Available legacy
imports remain warnings. Known missing staged `scripts.*` modules/private symbols
and recognizable unguarded reads of statically missing canonical paths stop before pytest, with
`test_status: preflight_failed` and an actionable `reviewer_support` message.
Fixed-depth paths that exist, guarded reads, and reassigned/fallback paths remain
warnings. The scan handles literal
`Path(__file__).resolve().parents[N]` expressions and simple assigned roots;
dynamic paths/imports still receive Python's normal test errors. Prefer these
helpers for canonical data and the public `Catalog.apply` API for reference
execution; keep task-specific probes local.

Before copying task source, `check --stage task_tests` probes Python 3.12+ and
imports pytest, NumPy and Pillow using the exact selected interpreter in an
empty directory, with inherited `PYTHONPATH`/`PYTHONHOME` removed and
`PYTHONNOUSERSITE=1`. Its receipt records interpreter/version, dependency
versions/paths and probe failures. Missing prerequisites or an unusable
interpreter produce `status: infrastructure_failed`, `passed: false`, unknown
test counts and no staged runtime; they are not generator test failures.
The receipt includes an executable setup command:

```bash
python3 -m venv .venv-review
.venv-review/bin/python -m pip install 'numpy>=1.26' 'Pillow>=10' 'pytest>=8'
PYTHONPATH=src .venv-review/bin/python -m arcpuzzles check TASK --stage task_tests
```

In a packet, supply `.venv-review/bin/python` to both the wrapper and its
Python payload. Keep isolation enabled; a user-site import by the wrapper
does not establish that the test child can import the same package.

## Opt-in strict scalar overrides

`ctx.draw_int_strict(label, lo, hi)` uses the same keyed RNG and provenance as
`draw_int`, but requires integer bounds and a Python `int` override. It rejects
booleans, floats and strings instead of coercing them; `None` retains the existing
no-override convention. Bounds remain inclusive and out-of-range values fail.
Existing `draw_int` coercion is unchanged for compatibility. Adopt the strict
helper where an axis needs that contract; this does not tighten old generators
or automatically rerun their checks.

`ctx.draw_color_strict(label, exclude={0})` adds the same literal-integer check
to color draws without changing legacy `draw_color`. Exact override observations
compare type and value; explicitly declared float axes retain numeric tolerance.
Defect lint now probes Boolean, float, string and negative scalar controls.

Create a new task-local canonical-input regression with
`python shared/tools/write_generator_test.py TASK --out generators/TASK/tests/test_canonical.py`.
It refuses an existing destination and uses `canonical_pairs`, `canonical_path`,
and `find_root`; it needs no legacy `scripts` namespace.


## Public challenge bytes and content IDs

New opt-in parametric writers can use the existing portable helper:

```python
from reviewer_support import public_challenge_bytes, public_challenge_id

payload = public_challenge_bytes(episode)
public_path = public_dir / ("challenge-" + public_challenge_id(episode) + ".json")
public_path.write_bytes(payload)
```

Only train inputs/outputs and test inputs are serialized. Visible grids must be
rectangular exact-integer colors0..9 within30×30. Private metadata, seeds,
parameters, programs and test answers cannot change these bytes or IDs. The ID
is the SHA-256 of exactly the file bytes, including its final newline. For a
batch, compute IDs first, reject duplicate visible payloads, then write in ID
order; keep private records separate. This is a projection/naming helper, not a
reference-label or lesson-identifiability gate. Existing dataset IDs are unchanged.
