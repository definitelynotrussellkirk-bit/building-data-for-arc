# Stop-short slide family — proposed

This opt-in adapter preserves the source puzzle's color binding and three motion
branches. Find a scatter's own-color 3×3 corner block, choose horizontal/vertical/
diagonal movement, find the canonical terminal cell, then stop `stop_short` steps
earlier. If the original path is shorter, stay at the source instead of reversing.
The canonical terminal can be next to the block **or at a grid boundary**.

| Parameter | Values | Canonical default |
|---|---|---|
| `stop_short` | exact integers `0`, `1`, `2` | `0` |

`program({"stop_short": 0})` returns the exact selected canonical Racket text.
Other settings change only its terminal placement. Python `transform` is a
parity aid; the writer executes protected Racket before publishing any files.
The canonical production generator, authorities, and approvals are unchanged.

## Use from the packet's outer directory

Activate its own environment once per shell. Do not substitute a sibling venv.

```bash
source WORK/.venv/bin/activate
python review.py run python3 generators/49c16a3506ab/workspace/parametric/artifact.py export \
  --seed 17 --demos 3 --queries 4 --out ../checks/new-stop-short-examples
python review.py run python3 generators/49c16a3506ab/workspace/parametric/artifact.py verify \
  ../checks/new-stop-short-examples --replay
python review.py run python3 -m pytest -q \
  generators/49c16a3506ab/tests/test_parametric_stop_short.py \
  generators/49c16a3506ab/tests/test_parametric_artifact.py
python review.py run python3 generators/49c16a3506ab/workspace/parametric/probe.py \
  --out ../checks/new-stop-short-probe
```

The export command writes all three settings, with the same inputs for the same
seed. Its destination must not already exist. `generate(seed, settings, demos,
queries)` is the native adapter interface. Counts are independent: 2–6 demos
and 1–4 queries; ordinary use is three demos and four queries. Settings, seeds,
counts, dimensions and indices reject Boolean/float substitutes for integers.

## Teaching and coverage

- Inputs have background 6 and two distinct colors, each with an opposite-corner
  3×3 block. Every color exposes row, column and diagonal motion.
- Demonstrations alternate main/anti layouts. Each sampled scene distinguishes
  all three stopping settings and color ownership from nearest-block motion.
  Two demonstrations already refute the orientation shortcut.
- A certificate fits three settings plus five named shortcuts at each setting:
  identity, blocks-only, cardinal-only, nearest-anchor and main-layout-only.
  Only demonstrations select survivors; query answers are never consulted.
- A certificate is finite hypothesis analysis, not grammar admission. The
  exporter independently validates every input and label before using it.
- The same setting-independent input RNG is used for every variant. Demo/query
  streams have separate indices; requesting more queries preserves earlier
  queries, and requesting more demos preserves existing demos and every query.
- Sampler dimensions are 9–30 on either axis. The four query shapes are 9×9,
  15×21, 30×30 and 21×30. Larger grids add more scatters, require central content
  and long paths, and retain the other-color block as a binding distractor.
  Collision freedom is enforced separately for all three settings.
- Placement is bounded at 96 attempts. Exhaustion or duplicate inputs raises an
  error; it never silently returns fewer queries. Independent review exercised
  160 size/orientation cases without failure, maximum six attempts. The native
  contract check exercised 30 episodes over two seeds and all demo counts.

This is contextual color binding followed by branch and endpoint calculation.
It does not simulate repeated actions reading a newly modified grid. No stronger
sequential-state or model-learning claim is made.

## Public, private and sequential files

`public/<sha256>.json` is a complete batch challenge with demonstration answers
and four **masked** query inputs. It is useful for batch consumers and inspection.
For sequential reveal, use `turns/<sha256>.json`, which contains the same
demonstrations and **one** masked query. The private `turn_ids` list specifies
their order. The existing controller decides when to release each file.

Only the single selected `turns/` payload goes to the model at each turn. It has
no total-count, index, last-turn or future-input fields. Its first-turn bytes and
content ID are identical to the corresponding one-query request. The utility
does not implement a controller or assume that writing files authorizes reveal.

All visible names hash the exact bytes from `reviewer_support`; seeds, settings,
programs and query answers cannot affect those names. `private.jsonl` retains
those fields and the query labels/certificates. Manifest IDs and private rows are
sorted by public content ID. Repeated visible episodes are rejected before any
publication. Writer validation failures leave no destination. A filesystem error
can leave an incomplete directory, which the verifier rejects without a manifest.

`verify` checks hashes, strict public grids, exact inventory, private grammar,
claimed labels, byte-exact certificates and turn projection. `--replay` also
re-executes all settings on demonstrations and the chosen rule on queries.
Serialized hashes establish local consistency, not external authenticity.

## Evidence and next owner step

`promotion.json` provides the native adapter contract. The generated
`evidence/manifest.json` binds current sources/tests and retained small receipts.
The return also retains a three-setting example export, a 30×30 witness, command
logs, 38 passing focused tests, and the 537-evaluation native/boundary probe.
The independent review's two verifier/import findings have regression tests.

These variants remain **proposed** and `training_admitted: false`. Owner source
qualification and explicit acceptance are still required before adding them to
the accepted parametric pool. Finite rivals and bounded seeds do not prove unique
induction or success on every future draw. No full canonical battery was rerun.
