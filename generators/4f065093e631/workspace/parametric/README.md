# Target-selection prototype for 4f065093e631

This is an **authoring prototype**, derived from original ARC training task
`890034e9`. It does not change the selected generator, its acceptance domain,
approval status, or the shared runtime API.

## Rule and parameter

The task still requires finding the unique largest nonzero monochrome rectangular
frame with an all-zero interior, deriving its height, width, and color, and finding
other same-sized zero-interior slots. The episode-level parameter changes which
matching borders receive the source color:

| `target_policy` | Executed transformation |
|---|---|
| `first` | Paint the first other matching slot in row-major order. This is the original/default setting. |
| `last` | Paint the last other matching slot in row-major order. |
| `all` | Paint every other matching slot, using the slots from the original input. |

These are the complete allowed values. Each episode binds one value once for its
three demonstrations and its query. `generate_episode(seed)` uses `first`;
`generate_episode(seed, target_policy=None)` draws the value once from a separate
deterministic seed stream. `build_evidence(seed)` explicitly materializes one
episode for each value, using shared input scenes for a controlled comparison.
Neither the query input nor a public filename encodes the hidden value. A
separate `public-file-order` seed stream shuffles the episode-to-number mapping
for each bundle; publication never resamples or changes the private episodes.

`materialize_program('first')` returns the current canonical Racket text **byte for
byte**. The other settings use guarded single-occurrence substitutions:

- `last`: `(target (fst slots))` becomes `(target (last slots))`.
- `all`: the same binding becomes `(targets slots)`; the final `paint-cells`
  receives the concatenated borders of `targets`.

Source finding, slot enumeration, frame ordering and all other canonical behavior
remain intact. If those exact fragments change, materialization fails explicitly
until a reviewer checks the new authority. Existing canonical scenes have one
other eligible slot, so all three settings agree there. The evidence separately
executes the default on every canonical train/test pair; agreement on those
anchors alone does not distinguish the proposed rule settings.

## Constructive scene scope

The sampler uses two rows of nonoverlapping tiles. It places a source and at least
two targets inside separate tiles; the remaining tile holds a smaller 3x3
monochrome frame. That smaller frame has a different color appearing exactly
eight times, fewer than the source's border cells. Selecting the rarest color
therefore does not identify the correct source.

Every matching interior is sealed by a nonzero border. Source borders are
monochrome. Target borders deliberately contain both noise colors, and every
target border cell differs from the source color. Background zeros are isolated,
so they cannot introduce a matching interior of height or width greater than one.
The selected generator's geometry helpers check the unique largest frame and
exact matching-slot set after construction. These helpers validate inputs; they
never provide saved labels. There is one constructive attempt per scene, with an
explicit error if an invariant is violated. There are no rejection or fallback
loops.

| Pair index | Role | Default canvas | Matching target count | Source frame |
|---|---|---|---|---|
| 0 | Demonstration | 18x21 | 2 | One of the four canonical dimensions |
| 1 | Demonstration | 21x18 | 2 | Next canonical dimension |
| 2 | Demonstration | 21x21 | 2 | Next canonical dimension |
| 3 | Query | 30x30 | 4 | 8x7 or 7x8, selected by the seed |

The canonical frame dimensions are 4x5, 5x4, 5x6 and 7x4. Colors, source/target
tile allocation, offsets inside tiles and noise cells vary deterministically.
The larger query increases both the frame dimensions and the number of eligible
targets. Its size generalization is more than empty padding.

The final production repair retains four calibrated 21x21 source/noise profiles
and exactly one eligible target. Even sample indices retain the original four
colors; odd indices add a fifth color on a disjoint smaller 3x3 zero-interior
frame whose eight cells make it rarer than the largest source frame. Independently,
the source color cycles through low, interior and high numeric rank, giving the
production teaching schedule a combined period of six. The prototype always
includes that kind of smaller frame, and broadens the input
distribution through multiple targets, varied canvas sizes and larger query
frames. The production generator's `self_check` is not claimed to accept these
prototype scenes. Its separately reviewed repair does not approve the proposed
rule settings.

`sample_scene(seed, pair_index, height=..., width=...)` honors exact integer size
overrides in 12..30 when the tile layout fits. The minimum height is twice the
source-frame height; the minimum width is twice the frame width for demonstrations
and three times the frame width for the query. An override that cannot fit this
layout raises `ValueError` before constructing a scene. Boolean sizes, noninteger
sizes, indices outside 0..3, and seeds outside the integer range 0..2**63-1 are
rejected.

## Run from a full review packet

From the outer extraction directory containing `review.py`, use the environment
prepared for this packet. The wrapper runs payload paths from `WORK/repo/`:

```bash
WORK/.venv/bin/python review.py run \
  /ABS/WORK/.venv/bin/python \
  generators/4f065093e631/workspace/parametric/target_policy.py \
  --seed 1729 --out ../checks/parametric/target-policy-s1729
```

Replace `/ABS/WORK/.venv/bin/python` with the absolute path to that same interpreter.
Alternatively, from `WORK/`, use its `run_with_racket.py` wrapper:

```bash
.venv/bin/python run_with_racket.py \
  /ABS/WORK/.venv/bin/python \
  generators/4f065093e631/workspace/parametric/target_policy.py \
  --seed 1730 --out ../checks/parametric/target-policy-s1730
```

Choose a new output directory for each invocation. Existing destinations are
refused. A successful invocation exits zero and prints one JSON summary. An
execution failure produces a private partial evidence report, omits all public
challenges, and exits one. Failed examples and bridge errors are retained rather
than silently dropped or relabeled. `--timeout` limits each Racket call, with a
hard maximum of 120 seconds; the generous default permits investigating the
unoptimized historical rule. It is not an estimate of the optimized rule's cost.

The same interpreter needs Python 3.12+, NumPy, Pillow and pytest for the portable
test suite. Racket and the prelude come from the packet. No network, sibling
checkout, copied runtime, or editable installation is required.

## Python API

The file is intentionally task-local; load it with `importlib.util` by its path
after the packet wrapper has configured the local runtime imports.

```python
program = prototype.materialize_program("last")
sample = prototype.sample_scene(1729, 0)
with prototype.Runtime(timeout=120) as runtime:
    output = runtime.execute("last", sample["input"])

episode = prototype.generate_episode(1729, target_policy="all")
evidence = prototype.build_evidence(seed=1729)
manifest_path = prototype.write_bundle(evidence, output_directory)
```

`Runtime` evaluates the exact lambda inside the canonical `rule!` registration
wrapper through the public `arc_repl.racket_bridge.RacketBridge` API. Every saved
output and rival prediction comes from that execution. No Python rule mirror is
used to assign labels. `generate_episode` is a convenience API that performs all
three-policy and canonical checks, so use `build_evidence` once when obtaining
several settings. `write_bundle` serializes the evidence returned by that API;
it does not independently certify externally fabricated dictionaries.

## Evidence and identifiability

The bundle contains:

- `evidence.json`: **private authoring data**, schema
  `arc-parametric-target-policy-evidence-v1`. It records task/parameter identity,
  source file hashes, exact Racket programs and hashes, seed, complete episodes,
  all rival predictions, every single-pair query holdout, canonical anchors and
  their executed outputs, command arguments, runtime identity, timings and
  genuine failures.
- `private/rules/{first,last,all}.rkt`: exact programs with no extra newline added.
- `public/challenge-001.json` through `public/challenge-003.json`: only
  `train: [{input,output}, ...]` and `test: [{input}]`. Public filenames are
  anonymous, their policy mapping is shuffled independently by seed, and the
  files omit parameters, seeds, IDs, programs, provenance,
  private diagnostics and query answers. Give only these files to a solver.

Source hashes map paths relative to the selected repository/runtime to SHA-256 of
their bytes. Program hashes bind exact UTF-8 text. Grid hashes bind UTF-8 encoding
of `json.dumps(grid, separators=(',', ':'), sort_keys=True)`. Public file hashes
bind the exact saved bytes, including the trailing newline. The canonical program
also has a separately labeled whitespace-normalized hash for comparison with the
existing shortened generator rule hash.

Each episode tests every policy on all four inputs. For the ordinary lesson,
indices 0,1,2 are demonstrations and index 3 is the query. The report then makes
each of the four pairs the query in turn, using the other three as demonstrations.
These are **query holdout rotations**, not spatial grid rotations. The source and
all matching slots are spatially varied by sampling; row-major first and last
are direction-dependent rules, so geometric rotation is not an output
equivariance requirement.

Every constructed pair contains at least two targets whose borders all change
when chosen. Consequently all three policies yield different predictions on
every pair, and holding out any one pair still leaves three distinguishing
examples. The report records `rejected_by_demonstrations`, `survived_all` or
`ambiguous` for each rival/holdout rather than simply claiming a passed census.
The selected policy is included as a self-consistency check. This is finite
declared-rival evidence, not a guarantee against every possible shortcut or a
claim about solver learning or training admission.

## Focused verification

From the outer extraction directory:

```bash
WORK/.venv/bin/python review.py run \
  /ABS/WORK/.venv/bin/python -m pytest -q \
  generators/4f065093e631/tests/test_parametric_target_policy.py
```

These tests cover exact default-program identity, strict parameter and size
contracts, deterministic constructive sampling without global-RNG changes,
independent border-based expected outputs, Racket-derived labels for every
policy, all canonical anchors, source/program/grid hashes, holdout
identifiability, strict public projections, and publication-order variation
across 32 seeds without changing any episode draws. They use
`reviewer_support.find_root`, `canonical_pairs`, and `load_selected_generator`;
they do not guess a fixed-depth canonical-data directory. Their scope is this
prototype, separate from the production generator's tests and admission checks.
