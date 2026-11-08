# Four-corner parametric prototype — 2692a3e47a66

This is a **separate prototype**, not a production parametric API or an approval
of the variants. The selected generator, canonical rule, catalog and runtime
contracts retain their authority. The implementation is local to this directory;
its focused tests are in
generators/2692a3e47a66/tests/test_parametric_2692a3e47a66.py.

## Parameters and preserved reasoning

| Parameter | Allowed literal integers | Original/default | Executed effect |
| --- | --- | --- | --- |
| min_repeat | 2, 3, 4 | 2 | A color moves when it occupies at least this many disconnected components. Pixel area is not the trigger. |
| step_blocks | 1, 2 | 1 | Multiply each selected object's own bounding-box height and width by this factor when translating it inward. |

Boolean values, floats, strings and out-of-range values are rejected. Parameters
are chosen once for an episode and remain fixed across all demonstrations and
the query. Calling plan_episode(seed) samples them deterministically once;
explicitly passing a Settings object supports exhaustive setting coverage.

The family keeps four solid square corner objects, color-7 background,
per-color component counting, inward movement, per-object measurement,
stationary colors below the threshold, and composition on the original canvas.
The programs still obtain objects from the original input, visit colors 0
through 9 in ascending order, erase a selected color's original cells, and paint
that color's translated objects. The original in-bounds clipping operation
remains in the Racket program.

Calling emit_program(Settings(2, 1)) returns the exact selected canonical
program_solution text. The other five programs replace only the component
threshold and/or the two displacement expressions. The normalized canonical
rule hash is pinned to **f5a9e05539e5**; an unexpected rule change fails closed.
No canonical source or rule text is rewritten.

## Input support and clearance

The prototype deliberately samples a narrower subset than the selected
canonical generator:

- Independent height and width in **25..30**.
- Exactly one solid square at each of the four exact grid corners.
- Side lengths **1..4**. The sampler additionally guarantees unequal sizes among repeated objects.
- Foreground palette **1, 2, 3, 4, 5, 6, 8, 9** and unique-modal background 7.
- Maximum color component multiplicity 2, 3 or 4. Multiplicity 2 includes both
  two pairs and a pair with two singleton colors.
- Input geometry and palette sampling are independent of the hidden setting.

For side \(s\le4\) and multiplier \(k\le2\), the original and destination cells
of a corner block lie inside that corner's envelope of side
\((k+1)s\le12\). Two opposing envelopes consume at most 24 cells. A dimension of
at least 25 therefore leaves at least one background row or column between
them. This guarantees no clipping, no inter-object destination collision, and
no source-erasure interference for **every one of the six settings**.

At most 64 of at least 625 input cells are foreground, so 7 is uniquely modal.
Objects cannot merge across envelopes under either 4- or 8-neighbor
connectivity. The input_errors function validates this safe structural subset;
uniform repeated squares also pass that validator. Unequal repeated sizes are
an additional sampler guarantee, exercised by the focused tests.

The diagnostic Python mirror also accepts smaller literal grids with
unique-modal background 7. This broader diagnostic entrypoint allows all five
canonical pairs and hand-derived overlap/painter-order checks. Those inputs
are not counted as lawful prototype samples. Color 0 is tested in those
diagnostics, but is not part of the prototype sampler's palette.

## Episode identifiability

Every production challenge contains **six demonstrations and one query**.
The demonstrations contain two inputs with maximum multiplicity 2, two with
maximum multiplicity 3, and two with maximum multiplicity 4, in shuffled order.
The seventh input has a seeded multiplicity from the same set. Every grid is
checked for uniqueness; duplicate grids are never counted to pad coverage.

For two settings \(a,b\), let \(D_{ab}\) be the set of input indices on which
their executed outputs differ. Every single-query holdout leaves a
distinguishing demonstration exactly when \(|D_{ab}|\ge2\). Here:

- The two multiplicity-2 inputs distinguish threshold 2 from thresholds 3 and 4.
- The two multiplicity-3 inputs distinguish thresholds 3 and 4.
- The two multiplicity-4 inputs distinguish both step values at every threshold.

Clearance and nonzero displacement prevent these differences from disappearing
through overwriting or clipping.

The implementation still **executes all six actual Racket programs on all seven
inputs of every episode**: 42 setting/input applications. It checks all 15
setting pairs for at least two differing inputs, and checks all six candidates
at all seven possible query placements. Each placement has one selected
setting and five alternatives. It reports both production placement 6 and the
six other holdouts.

The holdout checks reuse the 42 executed labels. Their 42 candidate-placement
comparisons and 35 alternative-placement comparisons are not extra Racket
applications or new examples. The prototype compares all 42 Racket outputs
against the independent Python mirror as an additional control.

These checks identify the selected setting within the **six declared programs**.
They do not prove that demonstrations exclude every other algorithm. Separate
hand-derived tests exercise component count versus area, per-object versus
global displacement, singleton stationarity, and painter order.

## Public API

| Entry point | Result |
| --- | --- |
| Settings(min_repeat=2, step_blocks=1) | Validated immutable setting. |
| select_settings(seed) | One deterministic setting. |
| emit_program(settings) | Exact Racket program for that setting. |
| sample_input(seed, sample_index, multiplicity) | One lawful setting-independent grid. |
| plan_episode(seed, settings=None) | Private plan with the fixed setting and seven distinct input draws; no manufactured labels. |
| input_errors(grid) | Errors against the narrower prototype input subset. |
| transform_mirror(grid, settings) | Diagnostic Python transformation; never the exported label source. |
| RacketLabeler() | Context manager owning one persistent included Racket bridge process. |
| generate_episode(seed, settings=None, labeler=None) | Returns complete private diagnostics after execution; public is None if ambiguity or a mirror mismatch prevents acceptance. Input and runtime exceptions propagate. build_evidence retains disk failure records for caught failures. |
| public_challenge(pairs, query_index=6) | Fresh projection with only train input/output and one test input. |
| audit_predictions(settings, pairs, predictions) | Finite candidate/holdout comparisons over complete executed labels. |
| build_evidence(out, seed=..., episodes_per_setting=1) | New evidence directory with programs, labels, source bindings and results. Existing destinations are refused. |

The implementation finds dependencies in its own repository or supported copied
runtime. It uses public reviewer_support helpers for canonical lookup and the
public RacketBridge methods define_grid, eval_text and shutdown for execution.
It does not call private runner methods.

The rule! form belongs to the authoring controller. The bridge adapter evaluates
the complete emitted program under a lexical identity binding for rule!,
producing the same grid function, and then applies that function through the
bridge. Every exact registration command is retained with its exact program
and SHA-256.

## Run

Use the packet's Python environment and included offline Racket runtime. From
WORK/, with the packet's writable temporary directory selected:

~~~sh
TMPDIR=/path/to/writable/tmp \
python3 run_with_racket.py python3 \
  generators/2692a3e47a66/workspace/parametric/prototype.py \
  --seed 20261019 --episodes-per-setting 1 \
  --out ../checks/parametric/evidence-final
~~~

Use a new output path for a retry; the tool refuses an existing directory.
Replace python3 with the packet's configured interpreter when needed.
The run_with_racket.py wrapper executes the payload from WORK/repo/, so do not
prefix the payload path with repo/.

The default evidence run emits one episode for each explicit setting using seeds
20261019 through 20261024, plus one automatically selected episode at seed
20261025. This is **7 episodes, 49 distinct episode inputs, 49 query-placement
checks, and 299 Racket applications**: 42 per episode plus all five canonical
pairs. Those are expected counts; a completed run's private report records the
actual observed counts and status. The episodes-per-setting option accepts 1..3
and records the corresponding finite seed set. Public IDs and export order use
independent fresh randomness; puzzle content remains reproducible for every
recorded seed and setting. The private manifest retains the exact mapping.

Focused tests, through the same supported wrapper:

~~~sh
TMPDIR=/path/to/writable/tmp \
python3 run_with_racket.py python3 -m pytest -q \
  generators/2692a3e47a66/tests/test_parametric_2692a3e47a66.py
~~~

Python-only controls can be selected with -k "not racket". Racket integration
tests are skipped when neither RACKET_PATH nor an executable racket is
available. A skipped integration test is not Racket parity evidence. The
supported wrapper makes the included runtime available.

Python 3.12+ and the packet's declared runtime dependencies are required; the
focused test command additionally requires pytest. The tool starts one Racket
process and reuses it, then shuts it down explicitly. Under memory pressure,
serialize this run with other Racket checks.

## Evidence and data separation

Only **public/challenge_<randomUUID>.json** files are model-visible challenges. Each has
exactly train and test keys. Demonstrations have input and output; the single
query has only input. Public filenames are independent UUIDs, and export order
is independently shuffled so ordering does not disclose the parameter list.
Public files are written only after all acceptance checks pass. Parameters,
seeds, query answers, reference programs, rival predictions and diagnostics
belong in private/.

Retained private files include:

- request.json: explicit build arguments and the actual invocation, saved before source lookup.
- plans/episode_NNN.json and plan_manifest.json: every fixed seed, setting and complete input plan, saved before Racket starts.
- rules/mN_sN.rkt: all six exact programs.
- episodes/episode_NNN.json: fixed settings, seed, realized draw indices,
  complete selected labels, all six candidates' outputs, program/source hashes,
  mirror comparisons and all query-placement checks.
- canonical_default.json: all five canonical pair identities, expected and
  actually executed default outputs, and equality results.
- witnesses.json: lawful same-input differences for the count threshold and
  displacement multiplier, with both executed outputs and rule hashes.
- source_snapshot/: the prototype, README and focused tests bound to the run.
- racket_trace.jsonl: actual application attempts, settings, input/output
  hashes, application expressions and errors, if any.
- report.json: actual command, effective cwd, runtime selection, source
  identities, precise counts, seed/setting coverage and declared limitations.
- failure.json on an ordinary caught failure. Completed partial episodes and
  the application trace are retained. A hard process kill may prevent writing
  the final report; the surrounding command receipt must retain that exit.

The initial feature-absence red, two reproduced failure-evidence defects, and
subsequent test executions are development
evidence, not solver failures. The outer review retains them under
WORK/checks/parametric/development/. Canonical repair checks, prototype checks,
approval and training admission are separate decisions.
