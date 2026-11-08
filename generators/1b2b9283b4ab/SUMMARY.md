# 1b2b9283b4ab

Rectangular rooms are separated by `1`/`9` walls and connected only where `7` doorways cross shared walls. Fill each room using shortest-path distance through that room graph. A seeded room contributes its smallest nonzero non-wall color. A tie between distinct nearest colors produces `8`; multiple nearest seeds of the same color produce that color. Preserve walls and doorways. Unreachable rooms use the canonical distance-`999` convention, so all global effective seed colors compete.

**Kind:** `per_puzzle`. **Current version:** `4.0.0` (imported `3.0.2`). **Canonical authority:** unchanged, rule ID `3e13418e96c9`.

The sampler covers chains, full grids, spanning trees, sparse graphs, disconnected rooms, repeated seed colors, and rooms containing multiple colors. Default four-draw windows use `[witness, canonical, witness, explore]`; three demonstrations and one query retain a compound witness under every tested query holdout. Exact controls are honored or rejected as incompatible; validation checks cells and graph geometry for every texture.

The [final battery](../../../checks/after-final/result.json) passes all 12 stages. The [final lesson census](../../../checks/lesson-census-final.json) checks 300 production lessons and 1,200 rotations without ambiguity against five unique declared rivals. These are bounded results: half the default draws share a compound witness topology, and sampled inputs use rectangular room lattices with seed colors `2..6` and no `8`.

See [notes.md](notes.md) and [DECISIONS.md](../../../DECISIONS.md) for controls, evidence, and limitations. The [tie-marker extension](workspace/parametric/README.md) is a separate proposed prototype. Approval is derived by the catalog from current code and retained evidence.
