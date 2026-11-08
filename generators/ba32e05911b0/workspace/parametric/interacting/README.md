# Rolling direction: native parametric prototype

Intent: retain the source puzzle's immutable-input collision decisions, exact
8/4/2/3 roll pattern, blocked/edge stops and sequential ledge traversal, while
inferring an episode-fixed `direction=right|left` from the demonstrations.
Right returns the exact canonical Racket bytes. Left conjugates that rule by
horizontal reflection, including reflected marker precedence.

The design uses constructive teaching scenes: a shared four-ledge cascade exposes route continuation, overlapping
paint and immutable collisions; a second scene teaches both boundary stops and
distal blockers. Fixed demonstration roles are part of the supported lesson API;
arbitrary train/query rotations are not claimed. No production generator or
canonical authority is changed.

## API and input grammar

`adapter.program(settings)` returns exact Racket text;
`adapter.generate(seed, settings, demos=3, queries=4)` returns private train/test
pairs and the program. Settings are exactly `{"direction":"right"}` or
`{"direction":"left"}`. Seeds are exact integers 0..2**63−1; counts are exact
integers, independently 2–6 demonstrations and 1–4 queries. Three demos is the
default; four is the recommended query count. Unsupported requests fail.

Inputs have 18–30 rows, 22–30 columns, literal-zero background, 2–3 bottom
magenta markers and orange ledges/distractors. The same seed/split/index has
identical inputs under both settings and all supported query counts. All
episode inputs are distinct. Separate RNG streams prevent count or private
direction from changing earlier inputs. The first 18×22 demonstration has
four sequential rolls; the second has both edge and distal exit-gap blockers.
The 30×30 query has three interacting markers, four rolls per marker, at least
198 orange cells, and structures/distractors spanning the canvas.

The canonical right rule processes markers left to right; reflected left
processes them right to left. Paint overlaps are intentional. Collision reads
always use the immutable input, even after an earlier marker paints a ledge.
The intermediate state is the current trace position, not a modified collision
grid. Each roll's input-dependent exit column chooses the next vertical ray
and thus the next contacted ledge.

## Run and verify

From the packet root containing `review.py`, use the selected Python interpreter:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/ba32e05911b0/workspace/parametric/exercise.py \
  --seed 17 --out ../checks/ba32e05911b0/new-exercise
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/ba32e05911b0/tests/test_parametric_contract.py \
  generators/ba32e05911b0/tests/test_parametric_adversarial.py
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  ba32e05911b0 --out ../checks/ba32e05911b0/new-qualification --summary
```

The exercise executes true and rival labels through protected Racket, checks
Python parity, replays the historical straight-climb teaching hole, exercises
the request boundaries, and writes two private four-query episodes plus eight
hash-named public files. Each public file contains demonstrations and **one**
query only. Give the controller the private episodes and reveal each public
query after the preceding answer; no turn controller is implemented here.
The first public bytes/ID match a single-query request and exclude private
settings, seeds, program text, query answers and every future query input.

## Measured evidence and limitations

`evidence/current/final-exercise/report.json`: 190 protected Racket executions,
six successful requests, zero failures; twelve rivals per direction, all
refuted by the two demonstrations. Rivals cover opposite direction, no roll,
stop on contact, caps at 1/2/3 rolls, ignored/partial blockers, mutable collisions,
reversed marker precedence and continuation without the roll displacement.
The 22 focused tests pass. Native qualification and causal replay receipts
are included separately under `WORK/checks/ba32e05911b0/`.

The original `exercise/` and `canonical-shortcut-review.json` record the
initial three-roll-demo version; they are retained as explicitly source-bound
pre-repair evidence. Review caught a cap-three shortcut, and the Racket-backed
regression failed before the first demonstration was strengthened to four
rolls. `final-exercise/` records the repaired source. The earlier 192-request
independent sampler sweep is not evidence for the repaired bytes.

The production sampler's seed-10 straight-climb gap is reproduced (35 wrong
query cells) and remains open in its original source. The separate parametric
sampler repairs this teaching issue. Canonical code, authority and approval are
unchanged. Finite rivals and sampled seeds do not prove universal uniqueness or
learning gains. Arbitrary holdout rotations are outside the API. Owner native
qualification and acceptance of the exact integrated source remain mandatory;
this reviewer return does not admit training data.
