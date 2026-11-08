# Fixed ascending-rank alternatives: v3.0.3

**The second-smallest rule leaves 8/300 production lessons and 30/1,200 query rotations ambiguous. Across fixed ascending ranks 1–5, the union is 10/300 production lessons and 41/1,200 rotations.** These results use the already completed public v3.0.3 census and its unchanged Racket labels.

## Exact family and counts

Each rival uses eligible green four-connected components, excluding an entire component if it touches row 0. It sorts by `(cell_count, earliest_occupied_coordinate)` and recolors the component at its fixed ascending rank. It leaves the input unchanged if that fixed rank exceeds the eligible count, matching the total diagnostic convention used for the earlier fixed descending ranks.

| Fixed ascending rank | Production ambiguous / 300 | Rotations ambiguous / 1,200 | Canonical train 0 | Canonical train 1 | Canonical test 0 |
|---|---:|---:|---|---|---|
| 1: smallest | 0 | 0 | No | No | No |
| 2: second-smallest | 8 | 30 | Yes | Yes | No |
| 3 | 1 | 7 | No | No | Yes |
| 4 | 1 | 4 | No | No | No |
| 5 | 0 | 0 | No | No | No |
| **Union** | **10** | **41** | — | — | — |

**None fits all three usable canonical labels.** Second-smallest fits both canonical demonstrations but fails the labeled test pair. These five are lesson diagnostics rather than additions to the set of rules fitting every canonical pair.

## Exact second-smallest counterexamples

The first production ambiguity is **medium lesson 11, seed 2940377972, requested start 11, accepted query sample 14**. The match vector is `[true, true, true, false]`. Two top-row blue cells request descending rank 2 among ascending sizes `[1, 2, 4, 6]`. Racket recolors the size-4 component at `(3,8), (3,9), (3,10), (4,8)`; the second-smallest rival recolors the size-2 component at `(5,6), (5,7)`.

The first second-smallest rotation ambiguity is **easy lesson 9, seed 127427506, start 9**, holding out pair **2**, accepted sample **11**. Its original match vector is `[true, true, false, true]`. The held-out input has three top-row blue cells and ascending sizes `[4, 5, 8]`. Racket selects size 4; the rival selects size 5.

[first-cases-v3.0.3.json](first-cases-v3.0.3.json) retains the complete original four-pair instances, exact inputs, unchanged Racket outputs, rival arrays, and pair features. The second-smallest cases are `cases.medium-11-query3` and `cases.easy-9-query2`, with `rival_outputs["2"]`. It also retains the first production and rotation cases for ascending ranks 3 and 4. Coordinates are zero-based.

## Reproduction and binding

[rescore.py](rescore.py) exposes `constant_smallest_rank(grid, rank)` using independent union-find. Its eligible component sets were crosschecked against the earlier independent DFS on all **1,108 distinct inputs**. The public `validate_retained_census` guard verifies completion, instance hashes, selected rule identity, and runtime manifest binding. The run exited **0**, meaning the rescore completed; the positive ambiguity counts remain findings. [Full report](rescore-v3.0.3.json) · [Console receipt](rescore-v3.0.3.log)

From `WORK`, with fresh output filenames:

```sh
TMPDIR=/dev/shm/arc-review-604d32c6dec0-tmp .venv/bin/python -B checks/ascending-ranks/rescore.py --out checks/ascending-ranks/replay.json --cases checks/ascending-ranks/replay-cases.json
```

| Binding | SHA-256 |
|---|---|
| Generator v3.0.3 | `9269425171b2ef8fe5b11d4e14006d54cf2cdd2f0a5ee7d4e20d8ce8ab533d4e` |
| Saved census | `8b37336252a71507098daa1379dc29f55a79a3d71a7ba63b2a32a0be952f8644` |
| Independent scorer | `ef71682eaea3502f132480badc6c1dde625666726e6dfc242ff7bcbcb385963d` |
| Rescore report | `abaceafe6f2f37a1c679b17202b5e5e258880694abf616cc80079593b9d15aa9` |
| Exact first cases | `f62d1377af15b6ed4780661f249f398d2491312b0636f800e4163ddfe6981869` |
| Selected Racket source | `53d5f7ffc0796769cee4ded45f1ffa203b7c126b599754ad91e0b375bc349e5b` |
| Executed Racket callable | `35dfefd5ec0d2dfc1e0ea111fa50a63e804b48b94d938384cbd32ac30e875a13` |

The final exact cases, counts, and canonical fits match the initial retained preliminary results. No new generation, reference execution, private episode access, or rival search beyond these five requested alternatives occurred. These measurements remain bound to v3.0.3; they do not certify a later repair.
