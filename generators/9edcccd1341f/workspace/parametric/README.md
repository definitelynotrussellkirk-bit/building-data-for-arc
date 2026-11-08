# Proposed prototype: episode-level frequency target

This task-local prototype adds one bounded rule parameter while preserving the
canonical keyed-frame reasoning pattern:

| Parameter | Allowed values | Default / original |
|---|---|---|
| `frequency_target` | `most_frequent`, `least_frequent` | `most_frequent` |

Both settings preserve the nonzero key row, inspect the framed interior, select
one color by its frequency, recolor the original outer frame with that color,
draw the selected cells' hollow bounding box, and clear the remaining interior.
Only the frequency extremum changes. `most_frequent` materializes the exact
selected canonical Racket text and retains rule hash `d1ac07400a65`;
`least_frequent` changes only the selector from `pick-max` to `pick-min`.

The shared prototype input subset is lawful under the selected production
validator and is independent of the hidden setting. It starts from deterministic
12×12 production draws with `winner_count=8` and `distractor_count=5`, then
collapses the three distractor colors to one already-keyed distractor color.
This gives exactly two candidate colors with a unique maximum and unique minimum;
both color sets must span at least two rows and columns. The original winner,
key row, frame, positions, and bounding-box reasoning remain unchanged.

A complete episode has four demonstrations and one query. The parameter is fixed
once before the five input draws. `build_episode(seed)` uses the canonical
setting, an explicit setting may be supplied, and `frequency_target=None` chooses
once through stable SHA-256. On retained inputs every demonstration rejects the
other declared setting. This is finite two-setting evidence, not a universal
identifiability claim.

## Exact runnable commands

Run from the extracted packet's outer directory. The wrapper selects the bundled
Racket runtime and executes payloads from `WORK/repo/`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/9edcccd1341f/tests/test_parametric_frequency_target.py

python3 review.py run python3 \
  generators/9edcccd1341f/workspace/parametric/prototype.py \
  --seed 173 --difficulty medium --start 0 \
  --out ../checks/parametric/frequency-target-s173
```

Use a fresh output directory for every evidence run. The CLI refuses to replace
an existing directory.

## Evidence layout

`public/episode-000/challenge.json` and `public/episode-001/challenge.json`
contain only four labeled demonstrations and one unlabeled query input. Public
files omit the hidden parameter, reference source, and query answers.

The private directory retains each episode's parameter, query answer, exact
Racket text and SHA-256, whitespace-normalized rule hash, selected generator
hash, accepted sample indices, input hashes, rival outputs, and demonstration
refutation indices. It also contains all-canonical-pair default parity and a
same-input disagreement witness. `private/manifest.json` records runtime status,
prototype source hashes, commands, and limitations.

Every label and rival prediction is produced by
`arc_repl.racket_bridge.RacketBridge`; no Python transformation mirror generates
answers. The lexical identity binding for `rule!` unwraps the authoring form and
executes the rule lambda against the bundled prelude.

## Scope and limitations

This is a **proposed prototype**. It does not alter `generator.py`'s production
sampling semantics, the canonical Racket authority, catalog pins, approval, or
training admission. The alternative applies only to the documented shared
strict-minimum subset. Evidence covers two settings, one retained five-pair
episode per setting at a chosen seed, and the other setting as the declared
rival; arbitrary hypotheses and all seeds remain untested.
