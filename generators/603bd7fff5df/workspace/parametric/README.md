# Native halo-depth parametric family

This task-local native adapter varies one episode-level parameter while preserving
the selected ARC family’s core sequential reasoning:

1. locate every gray (`5`) side marker and compute their bounding box;
2. keep that box’s columns and expand its row interval by the episode’s fixed
   `halo_depth` before extracting the output.

| parameter | allowed values | exact default |
|---|---|---|
| `halo_depth` | `0`, `1`, `2` | `1` |

`halo_depth=1` returns the exact selected canonical Racket source, byte for byte.
Depth `0` crops exactly the gray bounding-box rows; depth `2` retains two rows
above and below. The adapter supports independently requested lesson sizes of
2–6 demonstrations and 1–4 queries. Demonstration and query prefixes are stable,
inputs are matched across settings, and the fourth query is a substantive 30×30
case in the same `{0,5,8}` grammar.

The generator constructively exposes blue evidence in both possible halo rings
and an outside-column decoy. Thus all three settings and the declared shortcut
rivals are distinguishable from demonstration outputs, without revealing the
hidden setting in public challenge files.

## Native files

- `promotion.json` — finite adapter contract and count limits.
- `adapter.py` — native `program(settings)` / `generate(...)` entry point.
- `prototype.py` — deterministic sampler, teaching checks, public projection,
  and sequential-dependency counterfactual construction.
- `canonical.rkt`, `halo-depth-0.rkt`, `halo-depth-2.rkt` — exact rule programs.
- `audit.py` — reusable bounded prefix/count/rival/public-structure audit.
- `evidence/manifest.json` — current source/evidence inventory.

## Reproducible checks

From `WORK/`:

```bash
python3 ../review.py task-tests 603bd7fff5df --phase after \
  --out checks/603bd7fff5df-final-tests

python3 ../review.py run \
  python3 generators/603bd7fff5df/workspace/parametric/audit.py \
  --seed-start 0 --seed-count 256 --demos 2 3 4 5 6 \
  --out ../checks/603bd7fff5df/self-audit.json

python3 ../review.py run \
  python3 -m arcpuzzles parametric qualify 603bd7fff5df \
  --out ../checks/603bd7fff5df/qualification --summary
```

The retained finite audit covers 3,840 episodes and 30,720 labeled pairs with
zero failures. Exact protected-Racket qualification and the source-bound
counterfactual witness are retained under `WORK/checks/603bd7fff5df/`.

## Status and limits

This is reviewer-reported native-ready work, not owner acceptance. The finite
rival set and sampled seeds do not prove unique induction against every possible
rule. After integration, the owner must rerun native qualification, exact-source
acceptance replay, and any separate training-admission decision.
