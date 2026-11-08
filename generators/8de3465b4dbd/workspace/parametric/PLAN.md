# Native triggered-closure family

Preserve exact [2,3,0] -> [2,3,8] canonical behavior under `closure_policy=markers_only`. The alternative `newly_enclosed` first runs every canonical match, recomputes zero connectivity, then paints color 4 only in components that no longer touch a boundary but belonged to boundary-connected zero space before the matches.

Horizontal wall gaps carry exact patterns; their empty cell connects a room vertically to outside. Reverse [3,2,0] gates stay open; [2,3,3] blocked walls remain unchanged. Include preclosed rooms, two newly closed rooms, a partially closed two-gate room and non-sealing free triggers. The 30×30 query has six chambers. Do not use a vertical-wall gap whose preceding green cell already blocks access: that would make closure cosmetic.

Checklist: failing hand-derived tests; exact-source composition; constructive matched-input sampler; shuffled prefix-stable queries; executable teaching rivals/count/masking checks; frozen source manifest/native qualification/causal replay. No inherited test suite exists for this home. A task-local audit tool is copied and adapted, not imported from another task. No source outside this assigned home is changed.

Rejected simpler option: just projecting a ray from each new marker does not expose this strong changed-connectivity dependence. Rejected more complex option: multi-turn controller/training code is outside scope.
