# Working notes: 7092d9933e2d

## Current review decision

The selected canonical Racket rule is unchanged: each nonblank row is filled with its leftmost nonzero color, while blank rows remain zero. All retained canonical pairs replay under that rule.

The previous version advertised several ignored or misleading controls (`anchor_corner`, `asymmetry_force`, fixed-only palette/count axes, and degenerate textures). The repaired base generator now exposes only exact observable controls: `grid_h`, `grid_w`, `palette_kind`, `active_rows`, and `seeds_per_row`. It supports ordinary `difficulty=None` and `difficulty="medium"` draws required by authoring preflight.

The native parametric family adds `row_policy=bridge_equal`. Step A constructs the leftmost-color row-filled grid. Step B fills a blank row only when the nearest nonblank rows above and below in that intermediate have equal colors. The protected counterfactual uses rightmost rather than leftmost seeds for Step A; its final output differs.

Two demonstrations distinguish both settings from each other and from the finite named rivals (`rightmost_fill`, `rightmost_bridge`, `bridge_any`, and `global_first`) on seeds 0, 17, and 97. Four private queries include a substantive 30×30 case. This is bounded evidence, not a universal uniqueness proof.

Reusable next action: run `workspace/parametric/audit.py` through the protected-Racket wrapper, then perform owner exact-source review and fresh native qualification/acceptance. No approval or training admission is claimed here.
