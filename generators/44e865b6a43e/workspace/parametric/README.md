# Independent bar rotations — prototype

This task-local **prototype** varies two small rule parameters for original ARC
family `44e865b6a43e` (base record `2601afb7::44e865b6a43e`). It is separate from
the selected `generator.py`, canonical Racket authority, approval state, and
production generation API.

| Parameter | Allowed values | Canonical value | Meaning |
| --- | --- | --- | --- |
| `color_shift` | `-1`, `0`, `1` | `1` | Rotate the left-to-right color list |
| `height_shift` | `-1`, `0`, `1` | `-1` | Independently rotate the height list |

Positive means one position **right**, negative means one position **left**,
and zero leaves that attribute unchanged. The `(0,0)` variant is intentionally
the identity transformation. Both values are drawn exactly once from the episode
seed, before any pair is sampled, and then embedded in one immutable Racket
program for all three demonstrations and the query.

## Preserved reasoning and bounded input support

The learner still finds one-cell-wide, bottom-aligned solid bars on orange (7),
orders them left to right, extracts colors and heights independently, infers
each list rotation from demonstrations, and redraws the bars in the same columns.
Every scene has 3..5 bars in alternating columns with orange side margins, distinct
non-orange colors (including black), canvas height 7..12, and positive bar heights
strictly below the canvas height. These constraints are identical for all nine
parameter settings; they do not reveal the hidden rule.

At least three bars are required so offsets `-1`, `0`, `1` have distinct residues.
Distinct colors identify the color shift. Varied heights identify the height shift
unless the list is invariant under one or two positions of rotation. The sampler
excludes that ambiguity, including four-bar patterns such as `[a,b,a,b]` that
otherwise make the left and right height rotations agree. It does **not** require
all heights to differ: the second demonstration always repeats a height, and the
query samples heights with replacement subject to the same identifiability check.
The canonical source's repeated-height example is included in agreement checks.

The sampler is local to this prototype and does not call or change the selected
generator's sampler. Evidence checks every sampled input with that generator's
current `self_check` and hashes its current bytes. Thus a later canonical sampler
repair only requires new evidence; it does not silently change this prototype.

## Reproduce from an extracted packet

Run from the **outer extraction directory**, which contains `review.py` and
`WORK/`. Set `REVIEW_PYTHON` to the absolute path of this packet's prepared
`WORK/.venv/bin/python`; Python 3.12+, pytest, NumPy and Pillow are required by
the surrounding review environment. No installation or network is needed for
the included Linux Racket bridge.

```bash
REVIEW_PYTHON="$PWD/WORK/.venv/bin/python"
"$REVIEW_PYTHON" review.py run "$REVIEW_PYTHON" \
  generators/44e865b6a43e/workspace/parametric/prototype.py matrix \
  --seed 0 --out ../checks/parametric/matrix-replay

"$REVIEW_PYTHON" review.py run "$REVIEW_PYTHON" \
  generators/44e865b6a43e/workspace/parametric/prototype.py episode \
  --seed 7 --out ../checks/parametric/episode-seed7

"$REVIEW_PYTHON" review.py run "$REVIEW_PYTHON" -m pytest -q \
  generators/44e865b6a43e/tests/test_parametric_rotations.py
```

Use a fresh `--out` directory each time. `matrix` deterministically finds the
first seed for each setting at or above `--seed`; `episode` builds exactly the
requested seed. Both use `RacketBridge.eval_text` to execute the exact materialized
lambda, directly applied to a quoted integer grid. The Python mirror only checks
the live results. Every retained episode executes all nine candidate programs
on all four inputs and requires the three demonstrations to refute each of the
eight competitors. A rejected or failed episode raises an error, rather than
being silently retained with a passing verdict.

## Output separation and evidence

Only `public/challenge-<input-digest>.json` files are model-visible. The full
SHA-256 digest is computed solely from the ordered training input grids and
query input grids, grouped under `train` and `test`. Serialization uses sorted
keys, compact JSON separators, UTF-8, and one final newline. Labels, hidden
parameters, seeds, and emission positions are excluded, so changing any of them
while holding the inputs fixed leaves the filename unchanged. Matrix emission
is no longer sorted by the hidden setting. Duplicate input-derived filenames
within one output directory raise an error instead of overwriting a challenge;
use separate directories for different rules on the same inputs.

The files' top-level keys are `train` and `test`; demonstration pairs have
`input` and `output`, while queries have only `input`. Give a solver only the
selected public file, without the private folder. Earlier evidence directories
using numbered public filenames are superseded because their indices revealed
the hidden setting through the matrix's fixed sort order.

The `private/` folder retains all hidden settings, seeds, exact materialized
Racket programs and SHA-256 hashes, query labels, every candidate's live outputs,
demonstration refutations, source hashes, interpreter and runtime identity, and
the actual payload invocation. `canonical-agreement.json` retains the exact
canonical record and compares all four canonical labels with both the original
program and the prototype's canonical setting. `distinguishing-witness.json`
executes all nine settings on one lawful repeated-height input and requires nine
distinct outputs. `summary.json` records bounded counts and limitations. The
outer review command and its actual process exit are retained separately in
`WORK/checks/parametric/` by the reviewer.

The test suite covers rotation direction with manually specified expectations,
independent color/height motion, episode-fixed parameters, deterministic replay,
global RNG purity, all eight competitors for every setting, repeated heights,
canonical agreement, unsupported parameters, and strict public projection. An
end-to-end writer regression holds inputs fixed while changing the hidden rule,
both label splits, seed, and emission position; the public filename must remain
identical. It also checks that different inputs get different names and that
same-input collisions cannot silently overwrite files.
These are **prototype** tests, not canonical sampler repair or approval tests.

Passing this finite run exhausts the nine declared competitors on the retained
episodes only. It does not prove universal learnability, cover arbitrary rival
rules or all seeds, add a production parametric API, or grant training admission.
