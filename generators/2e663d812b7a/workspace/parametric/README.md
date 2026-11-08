# Proposed ring-metric prototype

**Status: prototype.** This task-local extension of `2e663d812b7a`
(`training:9356391f`) creates complete episodes under one fixed hidden rule
setting. It does not change the selected generator, canonical Racket authority,
production API, approval state, or training admission.

## Run the retained evidence

From the outer review-packet directory containing `review.py`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 generators/2e663d812b7a/workspace/parametric/prototype.py --out ../checks/parametric/evidence-final --seeds 2026102300 2026102301
PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 generators/2e663d812b7a/tests/test_parametric_prototype.py
```

The payload runs from `WORK/repo/`. The wrapper selects the supplied offline
Racket executable. Python needs only its standard library for this prototype
and its tests. A repository checkout outside the packet can invoke the Python
files directly after setting `RACKET_PATH` to its installed Racket executable.
The script discovers its own repository's reference bridge and canonical data;
it does not import a predecessor checkout or the selected input generator.

The output directory must be absent or empty. The exporter checks this before
creating directories, writing programs, or starting reference execution, and
raises `FileExistsError` for a nonempty destination. This prevents a later run
with fewer episodes from retaining and manifesting stale public challenges.
Existing output bytes remain unchanged on refusal. To replay after the retained
bundle is already present, choose a fresh path such as
`--out ../checks/parametric/replay-01`; the exporter never deletes old evidence.
The earlier `checks/parametric/evidence/` bundle and its original command
receipts are preserved as evidence from before this export safeguard.

The first command emits two complete episodes with three demonstrations and one
query each. Even seeds choose `chebyshev`; odd seeds choose `manhattan`. The
choice happens once at the episode boundary, independently of all input draws.
Use `--ring-metric chebyshev` or `--ring-metric manhattan` to fix a setting
explicitly for every requested episode. Reusing a seed under the other explicit
setting gives exactly the same inputs and different metric-dependent outputs.

## The bounded parameter

| Property | Declaration |
|---|---|
| Parameter | `ring_metric` |
| Allowed values | `chebyshev`, `manhattan` |
| Original/default | `chebyshev` — concentric square rings |
| Alternative | `manhattan` — concentric diamond rings |
| Input constraints that depend on it | None |
| Selection | Once per episode; deterministic seed parity or explicit override |

The original program reads a positional key from row 0, preserves the full gray
separator in row 1, and finds one seed in the lower canvas. Key index `d` supplies
the color at distance `d`. Internal zeros remain empty rings; repeated colors
retain their distinct positions. The original key supplies body colors even
after some header entries turn gray.

The alternative changes the body's distance from `max(abs(dr), abs(dc))` to
`abs(dr) + abs(dc)`. This is a small geometric rule change with the same seed,
key, ring composition, and boundary reporting. It changes predictions for the
same input; it is not an input-sampling variation.

Both metrics' radius-`d` rings contain the four axial points at offsets
`(+/-d, 0)` and `(0, +/-d)`. Those points attain each coordinate's extrema.
Consequently, a full ring fits in the lower rectangular canvas exactly when
`d <= min(seed_r - 2, height - 1 - seed_r, seed_c, width - 1 - seed_c)`.
The canonical clipping calculation therefore remains exact for the alternative.
Nonzero header entries beyond that radius turn gray; zero entries stay zero.
Partial rings are still drawn inside the canvas.

## Exact reference authority

`materialize_program("chebyshev")` returns the current canonical program string
byte for byte. The loader requires all canonical records for this task to agree.
`materialize_program("manhattan")` replaces one unique body-distance expression;
it refuses a canonical program whose expected expression is missing or repeated.
No clipping, header, key, or seed logic is replaced.

The build writes both exact Racket strings to `private/rules/` and hashes them.
`ReferenceRunner` evaluates each complete string through the included
`arc_repl.racket_bridge.RacketBridge`. A local lexical `rule!` registration
binding returns the program's lambda for application. All retained episode,
alternative-setting, witness, and boundary output grids come from actual Racket
execution. No Python model supplies a retained answer. The Python model is
used for nine named rival predictions and is checked against the executed
program on every episode input under both settings.

The default program is independently executed against the canonical program
on every retained episode input and on three boundary probes. It is also
executed against every stored canonical pair, retaining variant and split
identities and reporting the number of unique canonical inputs so duplicate
records are not counted as independent examples.

## Teaching design and size scope

Each episode contains these inputs, with fresh deterministic keys and selected
seed coordinates:

| Role | Size | Key length | Teaching purpose |
|---|---|---|---|
| Demonstration 1 | 16 x 16 | 6..8 | Top clipping, repeated entries, an internal zero, and a visible metric difference |
| Demonstration 2 | 19 x 21 | 6..9 | Complete rings; no spurious clipping report |
| Demonstration 3 | 23 x 27 | 10..13 | Rectangular canvas and right/bottom clipping |
| Query | 30 x 30 | 16..20 | Longer positional keys and rings on a canvas larger than every demonstration |

The prototype's parser accepts dimensions 9..30 and keys 1..20 (at most the
width), with nonzero endpoints, at most six distinct nonzero key colors,
color-0 lower background, a color-5 separator, and exactly one matching seed.
One-entry keys are supported for identity negative controls. The sampler uses
keys of length at least six. The extended keys above length ten are deliberately
**prototype-only input support**, outside the canonical generator's advertised
key domain. Larger examples change the visible ring extents and key positions;
their role is more than extra blank padding.

The first demonstration contains the diagnostic key prefix `[a, b, b, 0, c, d]`
and a seed at row 3. This exposes both the metric and the clipping boundary.
No query label is consulted to select demonstrations. Input draws are not
rejected or rearranged according to their query answers.

## Identifiability evidence and limits

For each retained episode, the other allowed metric is a setting rival whose
predictions are executed in Racket. Nine additional declared rivals model these
mistakes: using row 0 as the top boundary, consulting only the bottom boundary,
marking only the last key entry, marking zero key entries, dropping zero key
entries, deduplicating key colors, leaving the header unchanged, painting from
the marked header, and painting only complete rings. These semantic rivals use
the selected episode metric and change just the named behavior.

The report records the demonstration indices that refute each rival, whether
it changes the query, and any query-changing rival that fits all demonstrations.
An identity-only negative-control lesson in the tests must report ambiguity
when its query distinguishes the metrics. This is evidence against ten named
alternatives per episode, not a proof against every possible rule or all seeds.

## Evidence layout

- `public/episode-0000.json` and `public/episode-0001.json`: only `train` input/output
  pairs and `test` query inputs. No parameter fields, code, seeds, or query answers.
- `private/episode-*.json`: chosen setting, seed, all executed setting outputs,
  input observations, and the episode's rival audit.
- `private/rules/*.rkt`: exact programs and their hashes in `report.json`.
- `private/witness.json`: one lawful shared input and both executed outputs.
- `private/authority-equivalence.json`: canonical/default comparison results.
- `private/boundary-cases.json`: 9 x 9 corner, 30 x 30 opposite corner,
  and 30 x 9 rectangular probes, with both executed outputs.
- `report.json`: source hashes, runtime identity, executed payload command,
  per-execution status and input/output hashes, size counts, and limitations.
- `manifest.json`: hashes and byte sizes of the retained evidence members.

Only the files under `public/` are intended for a solver. The evidence directory
and private files are authoring/controller material. These finite checks do not
establish model performance or approval of the proposed Manhattan rule.

Public filenames are hashes of visible puzzle content, excluding private settings, seeds and query answers. Deliver only the public subtree; original reviewer sources and galleries are retained under `evidence/reviewer-original/`.
