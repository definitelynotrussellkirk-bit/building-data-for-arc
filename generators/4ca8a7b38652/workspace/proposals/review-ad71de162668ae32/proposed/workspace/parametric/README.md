# Scale-offset episode prototype — proposed, unapproved

The hidden episode parameter is one literal integer `scale_offset ∈ {-1,0,1}`.
For an input containing `n` distinct nonzero colors, expand every original pixel
into a `max(1, n + scale_offset)` square. Count colors, exclude zero from that
count, and preserve every pixel's position and value during expansion. These
reasoning steps remain invariant; the integer changes the executed rule.
The default `0` is the original task. `programs/offset_0.rkt` is byte-identical
to the selected canonical authority's `racket_target.target_code`.

This is a task-local authoring prototype. Canonical generator execution,
reference authority, approval hashes and shared runtime interfaces are unchanged.

## Exact runnable commands

Run from the packet's `WORK/` directory, retaining the `.venv/bin/python`
symlink itself as the payload interpreter (do not resolve it to the system
Python executable):

```bash
.venv/bin/python run_with_racket.py "$PWD/.venv/bin/python" \
  generators/4ca8a7b38652/workspace/parametric/prototype.py \
  --seed 23 --scale-offset -1 --query-side 6 --out ../checks/parametric/example

.venv/bin/python run_with_racket.py "$PWD/.venv/bin/python" \
  generators/4ca8a7b38652/workspace/parametric/prototype.py \
  --suite --out ../checks/parametric/suite

.venv/bin/python run_with_racket.py "$PWD/.venv/bin/python" -m pytest -q \
  generators/4ca8a7b38652/tests/test_parametric_prototype.py
```

The wrapper changes the payload cwd to `WORK/repo/`, selects the included Racket
and sets `PYTHONPATH`. Output directories must be new; prior evidence is never
overwritten. Omit `--scale-offset` to deterministically select one parameter
once per episode from its seed. The stable selector is the full SHA-256 integer
of `4ca8a7b38652/scale-offset/v1/{seed}`, modulo three, indexing `[-1,0,1]`.
The default mathematical setting is zero; omission deliberately requests the
seeded episode choice. Explicit offsets do not change the input draws.

If an execution fails, any already completed episodes remain available for
inspection; the suite summary is absent until the whole build succeeds. Treat
such a folder as partial evidence and retry with a new output directory. The
command's nonzero exit and log remain the failure record.

## Episode and input constraints

Each episode has five ordered demonstrations and one query. Demonstrations are
unchanged draws `sample_index=0..4`, difficulty `hard`, from the selected
canonical generator. They are 3x3, use two through four distinct nonzero colors,
and include both zero-present and zero-free examples with multiple color counts.
Every demonstration and query uses the same selected scale offset. Integer
seeds may be negative; booleans, strings and floats are rejected by the API.

`--query-side 3` uses the sixth canonical sampler draw. `--query-side 6` expands
the sixth draw's multiset fourfold and shuffles all 36 cells with a local,
deterministic RNG. It preserves the exact nonzero palette but introduces a
larger arrangement rather than spatially copying the 3x3 grid. This mode is
outside the canonical 3x3 teaching manifold. It changes no demonstration rules.
At most four nonzero colors and offset at most one give factor at most five;
the largest output is therefore 30x30. Only query sides 3 and 6 are supported.
The materialized rule itself also has defined identity behavior at factors
zero or one; the episode sampler intentionally retains `n=2..4`.

## Label authority and public/private separation

`RacketLabels` loads each exact `(rule! ...)` program into the existing protected
Racket bridge and applies it to the grid. The local `rule!` setter installs the
program's lambda; no transformation of the program source is performed. Every
retained demonstration, query and parameter-rival prediction is executed in
Racket. The Python mirror is a cross-check, never the source of labels.

Only `*/public/challenge.json` should be exposed to a solver: five input/output
pairs and one unanswered input. Private episode files contain the seed,
parameters, exact reference source and SHA-256, prototype/generator hashes,
query labels and rival checks. The suite summary also contains parameters;
it is private authoring evidence, as is `private/witness.json`.

The suite materializes all three settings at seed 23 with both query sizes,
plus seeded selections for seeds 0..5 with larger queries: twelve complete
episodes. It verifies default execution against all six labeled canonical
pairs and retains a single input producing output sides 3, 6 and 9 under the
three settings. Each episode records whether the demonstrations refute both
other offsets, fixed factors 1..5, count-all-colors, and all-colors-minus-one.
Refuting demonstration indices are retained, and query ambiguity is explicit.
Parameter rivals use Racket; simple shortcut rivals are Python hypotheses.

## Evidence and limits

`WORK/checks/parametric/COMMANDS.json` records actual commands, working
directories, exit codes, source hashes and evidence paths. The red test run
precedes implementation; the initial infrastructure failure is retained too.
`SUMMARY.json` binds the suite to its source and exact program hashes.

Measured scope is the finite retained seeds and the named rivals. No claim is
made for all seeds, arbitrary query rotations, every conceivable shortcut, a
production parametric API, or approval of the proposed alternative rules.
Canonical repair tests and prototype tests are separate scopes.
