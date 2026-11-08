# Horizontal collision-shift preference — prototype

This task-local prototype adds one bounded rule parameter to family
`b44c4c938f42` / original training task `337b420f`. It does not change the selected
generator, canonical Racket authority, catalog kind, approval, or training
admission. Canonical repairs and this proposed variant have separate evidence.

## Rule and parameter

`horizontal_shift_preference` has exactly two values:

| Value | Meaning |
|---|---|
| `left_first` | Original/default; the canonical program is returned byte for byte. |
| `right_first` | Reflect the horizontal coordinate of every shift in the priority list. |

The zero shift, vertical priority, panel splitting, unique-largest same-color
4-connected component selection, largest-first object order, collision and
bounds checks, and output background remain unchanged. Only the `shifts` binding
differs. Coordinates are `(row_delta, column_delta)`:

```text
left_first:  (0,0), (0,-1), (0,1), (-1,0), (1,0),
             (-1,-1), (-1,1), (1,-1), (1,1),
             (0,-2), (0,2), (-2,0), (2,0)
right_first: (0,0), (0,1), (0,-1), (-1,0), (1,0),
             (-1,1), (-1,-1), (1,1), (1,-1),
             (0,2), (0,-2), (-2,0), (2,0)
```

`random.Random(seed).choice(('left_first', 'right_first'))` selects the setting
once before drawing an episode. The same exact program labels all three
demonstrations and the one query. Seed 0 selects `right_first`; seed 1 selects
`left_first`. The input sampler does not receive the selected setting.

## Inputs and teaching evidence

Each source-generator draw supplies the input dimensions, separator columns,
panel count and palette. The prototype replaces its shapes with nested vertical
winners at one shared column, in a deterministic shuffled panel-size order.
Each panel also has a disconnected same-color singleton or domino smaller than
its winner. Thus the second-largest winner has two free horizontal choices.
This is a separate, narrower witness distribution, not the production sampler.

Every accepted pair must pass the selected generator's public `self_check`,
retain every selected component's color count under both programs, differ
between the parameter settings, and have an input distinct from the other pairs.
The default attempt budget is 64; the API accepts bounds from 1 through 256 and
raises on exhaustion instead of returning a short or ambiguous episode. A fresh
structural component-size count verifies survival; it never supplies labels.

The concrete 5-by-11 witness has a size-three vertical winner and an overlapping
size-two vertical winner, each with its own singleton distractor. After placing
the larger winner, the smaller winner moves left under the canonical program
and right under the alternative. Both outputs are retained with the input.

All labels come from `RacketBridge.define_grid` and `RacketBridge.eval_text`.
The public `strip_rule_wrapper` helper peels the wrapper, and the adapter binds
the documented body-form names `g`, `h`, and `w`. These pinned programs contain
ordinary Racket forms and need no shorthand normalization. The adapter is not a
general DSL normalizer. The broader `wrap_rule` helper currently requires the
staged-runtime `scripts.comment_solutions` import in this repository layout;
the earlier failure is retained rather than hidden by a runtime-tree copy.

## Run

From the **outer extraction directory** containing `review.py`:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/b44c4c938f42/workspace/parametric/prototype.py \
  --out ../checks/parametric/replay \
  --seeds 0 1 --bands easy medium hard

WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest \
  generators/b44c4c938f42/tests/test_parametric_shift_preference.py -q
```

The included packet wrapper selects the offline Racket runtime and runs payloads
from `WORK/repo/`. Use an output directory that does not exist. The local Python
environment needs pytest for tests; the current packet's `WORK/.venv` supplies it.
When those dependencies are available in the normal interpreter, `python3` can
replace both interpreter paths above.

## Retained checks and source binding

The final retained export is
`WORK/checks/parametric/final-evidence/manifest.json`. It records **6 episodes,
24 pairs, 6/6 production lessons, 24/24 query rotations, 12/12 canonical labeled
slots, and one concrete separating witness**. The 12 canonical slots contain
six distinct input/output pairs. Seeds 0 and 1 were checked in easy, medium and
hard bands, with three demonstrations and one query in each episode. Every
rotation leaves demonstrations that refute the other declared setting.

- `programs/left_first.rkt` and `programs/right_first.rkt`: exact materialized text.
- `public/challenge-000.json` through `challenge-005.json`: only demonstration
  input/output pairs and query inputs; no seed, hidden setting, program or query label.
- `private/episode-000.json` through `episode-005.json`: seed, fixed parameter,
  exact programs and hashes, every label and rival output, attempt records,
  source identities, live Racket identity, and all query-rotation checks.
- `private/separating-witness.json`: lawful concrete input and the two Racket outputs.
- `private/canonical-checks.json`: all canonical labels and actual default outputs.

The export binds selected generator version `3.2.0`, SHA-256
`33ce9d5349070343ba38e5386e00158382d482ba61f5e0683a71c276082f337a`.
It records the current generator source dynamically, while pinning the unchanged
canonical authority. Rehashing before and after generation rejects source drift
within an export. A future generator repair needs freshly generated evidence.

| Program | Normalized authority hash | Exact UTF-8 SHA-256 |
|---|---|---|
| `left_first` | `10339930cb51` | `c28d990306ed0cc7d8a1c3bb6c9bbb0db4012f9c53124a7b0dc137eca66c4707` |
| `right_first` | `b7afb2eb5ef7` | `58995312aa58a57859df4f37be9ba9b78d354d6c160f096a9cb617f993612d26` |

`WORK/checks/parametric/tests-final.json` retains the exact command and exit 0
for **16 passing prototype tests**. The prior missing-pytest attempt, the 16
expected missing-implementation failures, the `wrap_rule` dependency failure,
and the exhausted source-template sampler are retained in the same check folder.
The last of these accepted **0/4 from 64 draws** in the recorded seed/band runs:
the sampled version-3.1.0 source templates did not distinguish these shift preferences.
That observation motivated the explicit witness distribution above.

The task-owned `evidence/manifest.json` binds a compact retained proof, the
prototype, this README and its focused test. It is evidence of a proposed
extension, not an approval record. The receipt
`WORK/checks/parametric/retain-index-final.json` records its creation with
`WORK/checks/parametric/retain_index.py`; that helper checks every exported file
and live source hash before retaining the proof.

## Limits

Identifiability is measured only against `left_first` and `right_first`. It does
not establish identifiability against every extraction, object-order or shortcut
rule. The vertical witness distribution exercises the first horizontal tie;
the exact program diff establishes the specified reflection of the later
diagonal and distance-two priorities, but the episodes do not exhaust those
branches. No claim covers all integer seeds, every shape in the original ARC
task, or arbitrary rule parameters. Acceptance of the canonical repair does not
approve the alternative Racket program.
