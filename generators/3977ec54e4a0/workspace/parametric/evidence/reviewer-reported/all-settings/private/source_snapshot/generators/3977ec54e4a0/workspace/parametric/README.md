# Chevron parameters — proposed prototype

This isolated extension retains canonical marker grouping, chevron detection,
supported depth, and all four orientations. It does not change the selected
generator, canonical source, production rule hash, or approval status.

| Parameter | Values | Meaning |
|---|---|---|
| `fill_color` | `2, 4, 6, 8` | Actual Racket paint color; input palette stays `{0,1,3}`. |
| `fill_edges` | `true, false` | Include the two diagonal boundaries, or paint only their strict interior. Both retain the far-depth bound and every green marker. |

`Setting(8, True)` returns the **exact original program bytes**. Its full
SHA-256 is `b4c2540796af088ba41f486413b1be85ff6f8a9db373d30e6105bdc4529c7f25`.
The other programs apply guarded replacements to that pinned authority. No
input constraints depend on the parameters. The Python `predict` implementation
is an independent diagnostic; every label and every parameter rival prediction
comes from executing the matching Racket program.

## Run

From the outer extracted packet root, create all eight complete episodes:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/3977ec54e4a0/workspace/parametric/prototype.py \
  --seed 271828 --train 3 --test 4 --all-settings \
  --out ../checks/parametric/all-settings
```

The payload runs from `WORK/repo`; choose a fresh destination on reruns. A
single explicit canonical or alternative setting can be requested with:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/3977ec54e4a0/workspace/parametric/prototype.py \
  --seed 314159 --train 3 --test 4 --fill-color 6 --fill-edges false \
  --out ../checks/parametric/one-setting
```

Without parameter flags, a SHA-256 function of the seed selects one fixed
setting for the entire episode. A supplied flag overrides only that parameter.
`--all-settings` enumerates the eight settings with seeds `seed` through
`seed+7`; it cannot be combined with parameter flags. Separate `--train` and
`--test` controls accept `3..32` and `1..32`. Defaults are three and four.
`--max-attempts` defaults to 128 generated candidates and accepts `1..4096`.
Invalid scalars, stale canonical text, changed competitor inventories, source
changes during a run, and exhausted bounds fail visibly.

## Demonstrations and finite rivals

Inputs come from the current selected generator through public
`reviewer_support.load_selected_generator`. A deterministic sliding window of
demonstrations must eliminate all seven other executed parameter programs and
all eight canonical `LESSON_COMPETITORS`, adapted to the episode's paint color
and boundary choice. The adaptations are checked against the actual selected
Python declarations at the canonical setting on every candidate. These branch
competitors remain diagnostic Python programs; they are not reference labels.

Only after a window passes does sampling draw the requested distinct queries.
Every query is checked against rivals using those same demonstrations. No query
answer chooses, repairs, or enriches the demonstrations. Rejections and accepted
sample indices are retained. Every accepted input can be replayed with the
recorded seed, index, and `difficulty='medium'`. Inputs are unique within an
episode, including across its train/test boundary. Sampling failure returns no
shortened or cloned public challenge.

## Evidence layout

- `public/episode-NN.json`: only train inputs/outputs and test inputs. These
  neutral filenames do not encode parameters or seeds.
- `private/episode-NN.json`: fixed parameters, exact program, all outputs and
  rival predictions, accepted indices, source hashes, and finite-rival scores.
- `private/programs/`: all eight exact programs, including unchanged canonical
  text at the original setting.
- `private/canonical-parity.json`: real-Racket checks of all eight labeled
  canonical rows (four unique inputs).
- `private/diagnostic-probe.json`: an intentionally ambiguous lesson. Three
  complete-arm demonstrations hide edge inclusion, then one sparse-arm query
  distinguishes it. Both sets of labels are real Racket. This is a designed
  diagnostic, **not a naturally observed solver failure**.
- `private/report.json` and `private/source_snapshot/`: command, runtime,
  source manifests, exact prototype/selected-source snapshots, and limits.
- `private/failure.json`: honest failure details when a run cannot finish.

The retained authoring evidence for this review lives at
`WORK/checks/parametric/`, including red/green logs and `commands.json`.

## Focused tests

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest \
  generators/3977ec54e4a0/tests/test_parametric_chevrons.py -q
```

Tests cover canonical byte/label equality, all four orientations, both boundary
choices and all colors, all eight complete episodes, finite rival elimination,
index replay, determinism, fresh objects, public/private separation, validation,
bounded failure, and the designed ambiguity probe. These tests concern the
**prototype**; canonical scalar repair has separate coverage.

This is bounded evidence against a finite rival set. It neither proves
universal identifiability nor promises arbitrary query rotations, every seed,
or a uniform distribution. The production curriculum remains ordered.
