# Proposed `fan_stride` episode prototype

This task-local prototype keeps the production generator and canonical Racket authority unchanged. It adds one episode-fixed rule parameter:

| parameter | allowed values | original/default |
|---|---|---|
| `fan_stride` | `1`, `2` | `1` |

For every green seed rectangle, both settings keep the seed, advance one rectangle height downward per fan level, stamp symmetric left/right copies, clip at the canvas, and treat each seed independently. Only the horizontal displacement changes: level `k` uses `k × rectangle_width × fan_stride`. Setting `1` is byte-for-byte the canonical Racket source; setting `2` changes exactly the two horizontal-offset terms.

The setting is chosen once from the episode seed (even → `1`, odd → `2`) and stays fixed across every demonstration and query. The input grammar is shared by both settings. The evidence sampler uses the approved production input generator, cycles seed counts `3,2,1,3,2,1,3`, rejects duplicate inputs, and retains only lawful inputs on which the two declared settings visibly disagree. Demonstration and query counts are separate; the retained command uses three demonstrations and four distinct queries.

From the outer extracted packet directory, create the evidence bundle with:

```bash
python3 review.py run python3 generators/1856980929fe/workspace/parametric/prototype.py \
  --seeds 0 1 \
  --demo-count 3 \
  --query-count 4 \
  --out ../checks/parametric/1856980929fe-fan-stride-v1
```

Run the focused contract with:

```bash
python3 review.py run python3 -m pytest -q \
  generators/1856980929fe/tests/test_parametric_fan_stride.py
```

The writer fails closed if the output directory already exists. It records exact Racket text and hashes for both settings, canonical replay, deterministic private episodes, Racket-backed rival analysis, opaque public challenges derived only from visible bytes, and a second live-Racket verification pass in `verification.json`.

## Scope and limits

This is **proposed, unapproved prototype evidence**. It does not add a production axis, change the catalog, replace the canonical rule, refresh approval, or admit data to training. The finite evidence covers seeds `0` and `1`, the two declared stride settings, seven distinct lawful inputs per episode, and only the declared `fan_stride` rival. The sampler's visible-difference filter is an evidence convenience, not a new semantic input constraint.

## Additional branch-direction proposal

[branch_mode.py](branch_mode.py) ports the useful alternate axis from
`review-9802712d1af6ff45` beside the current stride prototype. It fixes one
`branch_mode=both|left|right` per episode; `both` is byte-exact canonical. This
changes which symmetric branch is painted, while `fan_stride` changes horizontal
spacing. Neither replaces the other or changes production generation.

```bash
python3 review.py run python3 generators/1856980929fe/workspace/parametric/branch_mode.py build \
  --seeds 0 1 2 --demos 5 --queries 4 --out ../checks/parametric/branch-mode
python3 review.py run python3 generators/1856980929fe/workspace/parametric/branch_mode.py verify \
  --out ../checks/parametric/branch-mode --rerun-racket
```

The current main stride writer emits the complete public batch in visible-ID
order. The branch writer also sorts before writing; focused tests bind both
implementations. Both remain proposed and unapproved.
