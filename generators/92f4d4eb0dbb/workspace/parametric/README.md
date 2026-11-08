# Proposed two-parameter midpoint-rule prototype

This directory is **not** part of the selected production path. The catalog
rule remains the original `lower` + `strict` behavior. The prototype explores
two bounded hidden parameters selected once per complete episode:

| Parameter | Values | Original/default |
|---|---|---|
| `side` | `lower`, `upper` | `lower` |
| `boundary` | `strict`, `inclusive` | `strict` |

`side` chooses which side of the color-1 occupied-row bounding-box midpoint is
recolored to 2. `boundary` decides whether an occupied integer midpoint row is
excluded or included. Every generated prototype pair has odd occupied height,
an occupied midpoint row, and occupied cells on both strict sides. Consequently
all four settings produce distinct outputs on every demonstration and query;
the demonstrations identify one episode-level setting rather than allowing it
to drift pair by pair.

Run from the packet `WORK` directory:

```bash
python3 review.py run python3 \
  generators/92f4d4eb0dbb/workspace/parametric/verify.py \
  --out ../checks/parametric/92f4d4eb0dbb-midpoint.json
```

The verifier writes exact Racket programs to `programs/`, complete retained
private episodes and answer-masked public challenges to `episodes/`, executes
every stored answer through the packet's Racket bridge, and checks every rival
setting against every demonstration and query. It also stores a source-bound
manifest in `evidence/manifest.json`.

Evidence is intentionally bounded: four retained episodes cover all declared
settings. This demonstrates a coherent, teachable task-local extension; it does
not approve a generic API, modify the selected catalog rule, or establish
all-seed behavior.
