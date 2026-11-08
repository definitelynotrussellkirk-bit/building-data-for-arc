# Reflection and overlay precedence — proposed prototype

This is a separate task-local authoring tool for family `576426a573af`. It does
not change the selected production generator, the canonical Racket authority,
approval hashes, or the production API. A successful prototype check grants no
production approval or training admission.

## Rule and parameter choices

Every rule reflects the original grid, then overlays two grids with zero as the
transparent background. Both reflection and overlay read the original input;
there is no iterative update. Colors and dimensions are preserved.

| Parameter | Allowed values | Default | Meaning |
|---|---|---|---|
| `axis` | `vertical`, `horizontal` | `vertical` | Vertical reverses row order (up/down); horizontal reverses column order (left/right). These names describe motion, not the geometric line of reflection. |
| `precedence` | `original`, `mirror` | `original` | At an occupied conflict, select the original or reflected color. If the preferred cell is zero, use the other cell. |

The four exact Racket programs are:

```racket
(rule! (grid-overlay-on (flip-ud g) g))
(rule! (grid-overlay-on g (flip-ud g)))
(rule! (grid-overlay-on (flip-lr g) g))
(rule! (grid-overlay-on g (flip-lr g)))
```

They are listed in vertical/original, vertical/mirror, horizontal/original,
horizontal/mirror order. The first program is byte-for-byte the canonical
`program_solution`, and the tool refuses to proceed if that identity changes.
All known labeled canonical pairs are checked through Racket. The original
reasoning remains recognizable in every setting: identify each reflected
partner, copy its nonzero color into a gap, and resolve an occupied conflict.
Axis and precedence are meaningful rule changes; palette and grid sizes are
ordinary input variation.

Explicit settings are fixed episode-wide. Use `sample` for either setting to
choose it once from the deterministic seed. Independent input streams depend on
seed, split, index, and retry count, never the chosen rule. All four settings
therefore receive the same inputs at a fixed seed and pair counts. Query draws
also remain unchanged when the demonstration count changes.

## Exact commands

From the packet's `WORK/` directory, this command emits two demonstrations and
four distinct, unlabeled query inputs under the default canonical rule:

```bash
python3 run_with_racket.py python3 generators/576426a573af/workspace/parametric/prototype.py --seed 17 --axis vertical --precedence original --train 2 --test 4 --out ../checks/parametric/single-export
```

This is the compact evidence command for all four complete episodes:

```bash
python3 run_with_racket.py python3 generators/576426a573af/workspace/parametric/prototype.py --seed 17 --train 2 --test 4 --all-settings --out ../checks/parametric/batch-export
```

To sample an episode rule deterministically, use
`--axis sample --precedence sample`. Both flags are resolved once before any
pair is drawn. `--train` accepts 1–16 and `--test` accepts 1–32; the defaults are
2 and 4. A single constructed demonstration already distinguishes the four
declared settings. Two demonstrations are retained by default for varied
teaching evidence. Counts are independent. Existing output directories are
refused, and uniqueness exhaustion fails explicitly instead of cloning inputs
or returning fewer than requested.

Focused tests, also from `WORK/`:

```bash
python3 run_with_racket.py python3 -m pytest generators/576426a573af/tests/test_parametric_overlay.py -q
```

The Python environment needs pytest for tests. Generation uses only the Python
standard library plus this repository's included protected Racket bridge and
its verified runtime. The review records the actual interpreter and command
arrays in `checks/parametric/public-identifiers-review.json`.

## Public and private files

For a single episode, give a solver only `public/challenge.json`. This fixed
relative path is retained for compatibility and encodes no setting or seed.
Its only keys are `train` and `test`; train entries have `input` and `output`,
while test entries have only `input`. A shared public projection copies exactly
those fields and excludes extra authoring metadata or query answers, even if a
caller adds them to the challenge object.

For `--all-settings`, the four episode directories are named
`episode-<SHA256>`, where the full digest is computed only from the exact public
challenge bytes: the visible projection serialized as JSON with sorted keys,
compact separators, and one final newline. Every batch directory contains the
same fixed `public/challenge.json` relative path. Both naming and directory
creation order depend only on those visible bytes; batches are written in
sorted public-identifier order. No setting ordinal appears in public paths.
Changing a private seed, parameter, reference program, or query answer while
holding visible content fixed cannot change the public path or public bytes.
Changing a demonstration input/output or query input changes its content-bound
identifier. Regenerating from a new seed may naturally change the visible grids
and therefore the identifier. Duplicate visible payloads fail before the batch
output directory is created instead of acquiring hidden-data or order suffixes.

`private/episode.json` contains parameters, program text and SHA-256, query
answers, accepted draw indices, input hashes and dimensions, and the complete
finite-rival report. `private/program.rkt` contains exactly the bytes hashed in
that report. The other private files retain canonical parity, a small contrast
witness executed under all four programs, the live protected-runtime identity,
and prototype/test/document hashes. The private summary associates each opaque
public identifier with its setting for reviewer traceability. In batch mode,
shared evidence is under the output directory's `private/` folder. Keep all
private folders and setting maps away from a solver. The caller chooses `--out`
and its ancestors; the writer cannot sanitize those external names, so expose
only the neutral single public path or the opaque batch relative paths.

Focused writer regressions execute the actual Racket-backed CLI for all four
settings and verify public schema, byte-bound names, hidden-data invariance,
visible-content sensitivity, enumeration and creation-order independence, and
duplicate refusal. These checks concern this proposed exporter, not canonical
generator approval or admission of the variant rules.

## Sampling and identifiability

The rule accepts rectangular ARC grids from 1×1 through 30×30 with integer
colors 0–9; booleans, ragged grids, empty grids and out-of-range values fail.
The authoring sampler deliberately uses a narrower teaching grammar:

- 3–6 nonzero colors and visible zero background;
- a random off-center reflected quartet with three different nonzero colors
  and one zero, protected while extra sparse cells are added;
- zero middle rows/columns on odd dimensions;
- a 10×4 first demonstration and later demonstrations with each side 4–14;
- query shapes cycling through 12×17, 21×13, 25×19, and 30×30.

The quartet guarantees a singleton and a conflicting pair for both axes.
Every sampled input distinguishes all four settings, a stronger restriction
than merely requiring the demonstrations jointly to identify them. It makes
the prototype easy to audit while avoiding setting-dependent input cues.
Additional occupancy grows with area; larger queries contain more active
cells, not just empty padding. No input constraint changes with the setting.
The generated default distribution is broader than the canonical 10×4 scenes;
canonical behavior is checked separately on the actual canonical examples.

`assess_lesson` accepts demonstrations and query **inputs**, never query
answers. It executes every declared program on each demonstration, rejects
programs with mismatching demonstration outputs, then checks the surviving
predictions independently for each query. Reports cite only demonstration
indices as refutations. All exported answers are actual Racket results; a
Python implementation is an additional cross-check, not the label authority.
The `rule!` registration wrapper is evaluated as its exact grid expression
with a lexical `g` binding through `RacketBridge.eval_text`; the normal bridge
security guards, startup checks and canaries remain active.

## Limits and status

This is **proposed prototype** evidence for four bounded settings, explicit
seeds and counts. Finite rival rejection does not prove universal
identifiability, model competence, calibrated difficulty, or training
eligibility. The forced quartet is a teaching restriction and a possible
distributional cue; a production extension should add independently specialized
demonstrations and assess less constrained query sampling. The canonical
family is a single reflection/overlay operation, so no sequential-state or
multi-rule reasoning claim is made. Query order is explicit; the tool checks
each query against the shared demonstrations and never uses another query's
answer as teaching evidence.
