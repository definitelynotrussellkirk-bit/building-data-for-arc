# Proposed destination-decoder parameter

This **prototype** varies one hidden episode-level rule parameter while keeping
c5905adcd2cb's source selection, global clearing, payload, and offset-copy logic
unchanged.

| Setting | Meaning | Status |
| --- | --- | --- |
| `direct` | Marker-local `(row, col)` selects destination macro `(row, col)`. | Canonical/default; exact canonical Racket authority. |
| `transpose` | Marker-local `(row, col)` selects destination macro `(col, row)`. | Proposed nearby alternative. |

The setting is selected once from the episode seed and is fixed across all
three demonstrations and two queries. Inputs do not depend on the setting. Each
demonstration uses an off-diagonal marker code, so the two declared programs
predict different destinations and the demonstrations identify the selected
setting before any query is answered.

## Run from the outer packet directory

```bash
python3 review.py run python3 generators/c5905adcd2cb/workspace/parametric/destination_decoder_episodes.py \
  --out ../checks/parametric/episodes --seeds 0 1
python3 review.py run python3 -m pytest -q \
  generators/c5905adcd2cb/tests/test_parametric_destination_decoder.py
```

The output directory must not already exist. Seeds `0` and `1` exercise both
settings. An explicit `--destination-decoder direct` or `transpose` keeps the
same fixed-seed inputs while switching the episode rule, enabling controlled
comparison.

## Reference execution and evidence

The tool loads the selected generator with `reviewer_support`, loads the exact
canonical training program from the canonical ledger, and derives the alternative
by swapping only the two destination-coordinate bindings. It executes both exact
Racket programs through the included persistent `RacketBridge`; there is no
Python label fallback.

`public/episode-*.json` contains only demonstration input/output pairs and query
inputs. It omits the seed, hidden setting, programs, source hashes, rival checks,
and query outputs. `private/` retains complete episodes and source-bound evidence;
`programs/` retains the exact executed Racket text. Every declared setting is
run over every complete episode, while identifiability is decided from the
three demonstrations only.

This is a bounded authoring proposal, not a production API or approval change.
It tests only the two declared destination decoders over finite retained seeds.
It does not establish uniqueness against arbitrary programs, and deliberately
leaves other possible coordinate maps out of scope.
