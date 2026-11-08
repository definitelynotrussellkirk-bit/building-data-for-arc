# Marker-column height prototype

**Status: proposed prototype.** This extends the original ARC
`training:72a961c9` family, task `c5dd8036311b`. It does not replace the selected
generator or change canonical authority, approval, or training admission.

## Rule and parameter choices

| Parameter | Allowed values | Original/default | Effect |
| --- | --- | --- | --- |
| `height_8` | integers 2, 3, 4, 5 | 3 | Number of added cells above each color-8 marker |
| `height_2` | integers 2, 3, 4, 5 | 4 | Number of added cells above each color-2 marker |

The transformation still locates a horizontal color-1 bar, locates its colored
markers, grows a column directly upward from each marker, repeats the marker
color at the top, and fills the remaining added cells with color 1. It preserves
the bar and all other input cells. Changing a height changes the executed rule.
Equal heights and reversed height ordering are supported: marker roles do not
depend on which color produces the taller column.

`choose_parameters(seed)` selects both values once for the whole episode.
`make_episode` uses that one materialized Racket program for every demonstration
and the query. Its optional explicit parameter argument supports fixed-setting
authoring. `build_input` never receives the hidden parameters and reserves five
rows above the bar so every setting is lawful; each pair has both marker colors.
The normal seeded API is deterministic: exposing or enumerating its seed can
also reveal its parameter selection. The stronger public-export protection
described below applies specifically to the crossed evidence suite.

The original/default setting preserves the exact canonical Racket text. The
materializer checks and changes only the two constants in
`(col-h (if (= color 8) 3 4))`. If the canonical expression changes in a future
checkout, materialization fails visibly and requires a review of the template.
All outputs are produced by the included protected `RacketBridge`. No Python
mirror is used as a label authority.

## Run a complete evidence suite

Run from the packet's `WORK/` directory after `python3 setup_racket.py`:

```bash
python3 run_with_racket.py python3 \
  generators/c5dd8036311b/workspace/parametric/build_evidence.py \
  --out ../checks/parametric/height-suite-v2 \
  --seed-start 0 --episodes-per-setting 2 --train 3
```

Use a new output directory for every run. The wrapper runs the payload from
`WORK/repo/`; paths after the wrapper refer to that directory. The tool requires
only the packet's Python runtime, portable canonical helpers, and Racket. It
does not import or execute the selected generator, so canonical sampler repairs
cannot silently change this prototype's labels or input distribution.

The command crosses each of the 16 explicit, episode-fixed settings with the
same input seeds `seed_start + j`. With the command above, input seeds 0 and 1
each occur under every setting. It writes 32 complete episodes, each with three
demonstrations and one masked query: 128 labeled pairs on eight unique input
grids. Even recovering an input seed from its grid leaves all 16 settings
possible before reading the demonstrated outputs. `--episodes-per-setting`
accepts 1..8 and `--train` accepts 1..7. Every generated pair distinguishes every
setting, so one demonstration is sufficient within this parameter family.

The following checks run before a completed manifest is written:

- The default Racket program exactly matches the canonical text and all five
  original labeled input/output pairs.
- Every episode's labels are reproduced by its one fixed program.
- All 16 materialized settings are executed on every retained episode input.
- Every possible single-query holdout leaves exactly the selected setting
  consistent with the remaining demonstrations.
- One common lawful input produces 16 distinct outputs across the settings.
- Every input-seed replica has exactly the same input tuple under all 16
  settings, closing the setting-specific seed-lookup channel.
- A negative control omits color 8 from its demonstrations and includes it in
  its query. Four settings fit those demonstrations; three give a wrong query
  answer. The checker must report those ambiguities.

The tool retains any exception in a failed manifest instead of calling a partial
run complete. It refuses an existing output path so reruns preserve evidence.

## Files and visibility

Give only the `public/` directory to a visible-example solver. Its complete
metadata contract is:

- `index.json` has exactly one field, `challenges`, containing a shuffled list
  of challenge filenames. The count of files and their random order are visible.
- Each challenge filename is 32 hexadecimal characters generated from 128 bits
  of fresh OS randomness, followed by `.json`. IDs are independent of settings,
  seeds, content, and private episode order. They are not hashes of enumerable
  seeds. A separate OS-random shuffle runs before any public file is written,
  preventing setting grouping through creation order or timestamps.
- Each challenge JSON has exactly `train` and `test`. Demonstrations contain
  `input` and `output`; the single query contains only `input`. Their integer
  grids, dimensions, pair order, and visible outputs are available for reasoning.
- Parameter values, seeds, private episode indexes, reference code, query
  answers, the root `manifest.json`, and all files in `private/` are withheld.

Re-exporting the same episodes produces identical challenge content and fresh
public IDs/order. The exact current ID mapping is retained privately, while
settings, input seeds, source hashes, and materialized programs make content
reproducible. The same input grids intentionally recur across settings; the
demonstration outputs teach which setting governs the query.

The rest of the evidence tree is controller-only authoring data:

| File or directory | Contents |
| --- | --- |
| `manifest.json` | Commands, effective cwd, status, seeds/settings, source and artifact SHA-256 hashes, counts, limits |
| `private/specification.json` | Parameter contract, preserved reasoning structure, rule paths and hashes |
| `private/rules/*.rkt` | Exact materialized Racket text for all 16 settings |
| `private/episodes/*.json` | Parameters, seed, fixed program, complete labeled pairs |
| `private/identifiability/*.json` | Actual Racket predictions for every setting and every query-holdout result |
| `private/input-independence-check.json` | Each input seed crossed with all 16 settings, with identical-input hashes |
| `private/public-export.json` | Private mapping from internal episodes to random public filenames and shuffled index positions |
| `private/canonical-default-check.json` | All five original pairs and executed default outputs |
| `private/setting-difference-witness.json` | Common lawful input and 16 distinct executed outputs |
| `private/negative-control-*.json` | Exact undercovered lesson and its detected ambiguities |
| `private/source/` | Exact authored source, README, and test snapshots used by the run |

`manifest.json` hashes every retained artifact other than itself. Rule hashes are
SHA-256 of exact stored text. The canonical normalized short rule hash is also
recorded separately for comparison with the selected generator's authority.

## Focused tests

The tests are in `tests/test_parametric_heights.py` and
`tests/test_parametric_public_privacy.py`, outside the frozen fixture.
They cover parameter validation, actual Racket tip/stem behavior at boundary and
equal/reversed heights, input preservation, canonical parity, deterministic
episode construction, every setting under every holdout, negative-control
ambiguity, public/private projection, opaque public filenames and index schema,
matched inputs across settings, and fresh IDs on content-preserving re-export.

From `WORK/`, using the packet's prepared interpreter:

```bash
python3 run_with_racket.py ../.venv/bin/python -m pytest -q \
  generators/c5dd8036311b/tests/test_parametric_heights.py \
  generators/c5dd8036311b/tests/test_parametric_public_privacy.py
```

An absolute path to a Python interpreter with pytest also works. If no virtual
environment was prepared, use an interpreter with pytest installed. The normal
task-test stage is a separate aggregate gate and may also include inherited
tests; this focused result is only prototype coverage.

## Superseded evidence

`checks/parametric/height-suite-v1/` remains unchanged as source-bound evidence
of the initial implementation. Its labels and finite-rival checks passed, but
its public sequential filenames encoded sorted parameter order. Its search for
setting-specific seeds also allowed a grid-to-seed lookup to identify a setting.
The initial JSON-field audit did not detect these metadata channels. Do not use
the v1 public files as a hidden-setting challenge set.

The v2 repair retains actual failing regressions in
`checks/parametric/v2-privacy-red.{json,log}` and creates new evidence in
`checks/parametric/height-suite-v2/`. The setting/input crossing, opaque names,
and shuffled write/index order address these observed channels. They do not
make the ordinary deterministic episode API private under arbitrary seed
disclosure or claim information-theoretic secrecy of the visible examples.

## Boundaries

The supported input domain has one full-width horizontal bar, a zero background,
markers of colors 2 and 8, and sufficient room for complete columns. Generated
episodes always include both marker types and contain no distractors. All 16
bounded parameter settings are checked on the retained samples. This finite
rival check does not establish uniqueness among arbitrary programs or approval
for production generation. Query holdout rotations rearrange train/test roles;
they do not rotate the grids geometrically. Geometric rotation would change the
family's upward-only rule and is not one of these parameters.
