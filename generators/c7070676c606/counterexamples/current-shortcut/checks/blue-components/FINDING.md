# Observed blue-component shortcut: v3.0.2

**The observed rule fits all three canonical pairs but leaves 31/300 retained production lessons and 122/1,200 required query rotations ambiguous.** This reproduces a concrete limitation of the v3.0.2 lesson family on existing public Racket labels.

The rival comes from the finished public solve receipt `../final-solve-v3.0.2.json` and its archived `../prior-solve/v3.0.2/solution.py`. It counts four-connected blue components over the entire grid, sorts four-connected green components by descending cell count and earliest occupied cell, and recolors the object at that rank. Undefined ranks leave the grid unchanged. The exact observed solver includes green components touching row 0; the independent mirror preserves that detail. It does not inspect any private evaluation data.

## Bounded measurements

| Scope | Production ambiguities | Rotation ambiguities |
|---|---:|---:|
| Easy | 15/100 | 40/400 |
| Medium | 8/100 | 49/400 |
| Hard | 8/100 | 33/400 |
| **Total** | **31/300** | **122/1,200** |

The rival is refuted by demonstrations in 121 production lessons and 486 rotations; it agrees on all four pairs in 148 lessons and 592 rotations. Ambiguity means agreement on every demonstration followed by disagreement with the held-out query. The independent union-find implementation agrees exactly with the archived solver on all **1,106 distinct labeled pairs**, plus the three canonical pairs. Only the saved Racket outputs determine correctness. The canonical top-row cell counts and global blue-component counts are both `[2, 3, 2]`, explaining its 3/3 canonical fit.

## Exact first production and rotation case

Both first cases are **easy lesson 0, seed 1753406524, requested start 0, query index 3, accepted sample index 3**. The full instance, exact input, unchanged saved Racket output, and exact rival output are retained in [first-cases-v3.0.2.json](first-cases-v3.0.2.json), key `cases.easy-0-query3`.

| Pair | Top-row blue cells | Global blue components | Rival matches Racket |
|---|---:|---:|---|
| Demonstration 0 | 2 | 2 | Yes |
| Demonstration 1 | 3 | 3 | Yes |
| Demonstration 2 | 2 | 2 | Yes |
| Query | 3 | 1 | **No** |

The query's ranked green sizes are `[7, 5, 3]`. Its three adjacent blue cells form one component. The Racket output selects size 3, changing `(19,1), (19,2), (20,2)` from 3 to 2. The rival selects size 7, changing `(5,11), (5,12), (6,9), (6,10), (6,11), (6,12), (7,11)`. Coordinates are zero-based. The matching demonstrations permit the component-count interpretation despite the query's different grouping of markers.

## Reproduction and source binding

[rescore.py](rescore.py) loads the public `validate_retained_census` guard, validates the saved runtime/instance bindings, and extracts only the observed solver's pure `solve` definition for comparison. It independently predicts with union-find. The run exited **0**, meaning the analysis completed; the ambiguity counts remain positive. [Full report](rescore-v3.0.2.json) · [Console receipt](rescore-v3.0.2.log)

From `WORK`, with new output filenames:

```sh
TMPDIR=/dev/shm/arc-review-604d32c6dec0-tmp .venv/bin/python -B checks/blue-components/rescore.py --out checks/blue-components/replay.json --cases checks/blue-components/replay-cases.json
```

| Binding | SHA-256 |
|---|---|
| Census generator v3.0.2 | `3233c9098c6fe58a4f433372f0116ffbd8cc1583f7a81a15bf1c0ae210ed1675` |
| Saved census | `36effef53ffe0c3ec7e3c9ff01e169808f562e2c55096463d9da7217abb40bc0` |
| Observed public solver | `5500d7ec4c76cead6d47bb4dd7de51c01772772ccc7731ad4a418e46f351f289` |
| Independent scorer | `85681179eafc2b668769c5bcd427a22a71a8149c80ab0a03f69409c4032fc5d1` |
| Rescore report | `b7f51011de6cdf2f715eac2fa8863c6fb1bbed825930c6eb70672610f8bd06ad` |
| Exact first cases | `c272b6e7678a849aca7489906c1e01682f355beeb68f57d281d89d9f3dd32efe` |
| Selected Racket source | `53d5f7ffc0796769cee4ded45f1ffa203b7c126b599754ad91e0b375bc349e5b` |
| Executed Racket callable | `35dfefd5ec0d2dfc1e0ea111fa50a63e804b48b94d938384cbd32ac30e875a13` |

The live generator had advanced to v3.0.3 (`92694251…`) when the retained scorer ran. The report explicitly records the mismatch; these measurements apply to v3.0.2. No new generation, reference execution, runtime snapshot, or additional rival search was performed. Verification of the repair requires its own source-bound evidence.
