# 786a759f780e

Find every 4-connected component made from nonzero cells; colors may mix inside one component. Crop each component to its bounding box, count enclosed zero regions inside that box, and sort components by `(hole count ascending, painted area ascending, first row-major component color ascending)`. Pack the sorted crops left-to-right, top-aligned, with one black separator column.

The generator uses three scheduled teaching profiles:

- `canonical_holes`: canonical 0-, 1-, and 2-hole morphology.
- `hole_priority`: area and hole count disagree, so area-only sorting fails.
- `tie_chain`: equal-hole objects expose area ascending and the final color tie-break.

Every ordinary generated scene contains a mixed-color component and presents components in a reading order different from the answer order. Exact supported controls are `scene_profile=canonical_holes|hole_priority|tie_chain` and `canvas_profile=11x20|12x20`.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical `RULE_HASH`: `71abd31a186f`. `EXAMPLES_NEEDED=5`.
