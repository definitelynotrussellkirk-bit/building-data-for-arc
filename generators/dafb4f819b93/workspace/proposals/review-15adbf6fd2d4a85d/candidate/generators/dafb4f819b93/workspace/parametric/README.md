# Proposed label-offset parameter prototype

Status: **proposed and unapproved**. This workspace does not modify the selected
production generator, its canonical rule, or `RULE_HASH`.

The episode-level parameter is `label_offset` with bounded values:

- `0` — canonical/default: paint an interior cell when its row and column border
  labels are the same;
- `1` — proposed variant: order the distinct colors by their right-border runs,
  then paint when the column label is the next color after the row label, wrapping
  cyclically from the last color to the first.

Both settings keep the same square border-only inputs, shared ordered palette,
row/column label extraction, preserved nonzero borders, and row-label paint color.
The input constraints do not depend on the parameter. The setting is selected
once from the episode seed and remains fixed across every demonstration and
query.

## Run the exact four-query evidence build

From the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/dafb4f819b93/workspace/parametric/prototype.py \
  --seeds 1 0 --n-train 3 --n-test 4 \
  --out ../checks/parametric/dafb4f819b93-label-offset-v1
```

Seeds `1` and `0` exercise offsets `0` and `1`, respectively. The output path
must be new. Every demonstration and all four query labels are produced by
executing the matching materialized Racket source through `RacketBridge`.

Focused tests:

```sh
python3 review.py run python3 -m pytest -q \
  generators/dafb4f819b93/tests/test_generator_dafb4f819b93.py \
  generators/dafb4f819b93/tests/test_parametric_label_offset.py
```

Verify an existing evidence tree without rewriting it:

```sh
python3 review.py run python3 \
  generators/dafb4f819b93/workspace/parametric/prototype.py \
  --verify-only --out ../checks/parametric/dafb4f819b93-label-offset-v1
```

## Evidence boundary

`public/challenge-<sha256>.json` contains only visible demonstration inputs and
outputs plus query inputs. The filename is derived from those exact visible
bytes; hidden parameters, seeds, Racket source, private ordinals, and query
answers cannot affect it. `private/` retains the setting map, query answers,
source hashes, exact Racket programs, selected-generator draw provenance,
canonical replay, and a distinguishing witness. `manifest.json` binds every
retained evidence file.

The verifier re-hashes the tree, reconstructs public projections, rejects public
ID collisions, reruns every saved label in Racket, and repeats canonical replay.
This is finite evidence against the other declared offset only. It does not prove
unique induction against arbitrary programs, approve a new variant, or admit it
to training.
