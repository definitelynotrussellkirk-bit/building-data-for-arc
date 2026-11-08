# fbf36c193fa6

A 16..23 by 16..23 zero-background grid contains one solid 3x3 cyan(8) square and 20..64 gray(5) obstacles. Red(2) rays leave the four square corners on the outward diagonals, stopping before a diagonal gray cell or before a diagonal cell pinched by gray cells on both inward orthogonal sides. Yellow(4) rays leave the corners in the clockwise-adjacent diagonal directions as alternating staircases: gray at the start suppresses the ray, gray on an intermediate step stops before it, and gray on the next diagonal cell preserves the intermediate step before stopping. Gray and cyan cells remain unchanged.

Ordinary same-seed consecutive draws use an open/mixed/mixed cycle. The two mixed scenes have opposite blocker orientations, so each three-example window exposes both upward and downward corner-pinch stopping plus open controls. Seed parity covers all four orientations across seeds. Blocker distances vary over legal ray steps. This lesson guarantee does not cover shuffled examples, independently reseeded examples, or forced profile overrides.

Kind: `per_puzzle`. Selected version: `4.1.0`. Rule pin: `df658022eba5` (unchanged).
Approval remains derived by the catalog from current code and retained evidence; this review is not maintainer approval or evidence of model accuracy improvement.

## Task-local parametric prototype

`workspace/parametric/` adds a native adapter for `yellow_turn ∈ {clockwise, counterclockwise}`. Clockwise is byte-exact canonical; the alternate changes only the yellow corner-to-diagonal assignment. The sampler supports 2..6 demonstrations and 1..4 stable-prefix queries, keeps inputs identical across settings, includes a centered 30x30 stress query, and exports exact canonical public bytes under `challenge-<full-sha256>.json` while query answers remain private. Focused tests pass 7/7, staged task tests pass 26/26, and native qualification covers both settings at seeds 0 and 17. The current manifest is `0a5b9e9ed63b6e6035865435bb1c56277157bf37e1706f86ac4e0eb465340eb6`. This prototype is qualified evidence, not acceptance or training admission.
