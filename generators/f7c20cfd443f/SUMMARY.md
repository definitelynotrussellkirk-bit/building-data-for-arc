# f7c20cfd443f

A black input grid contains isolated singleton gray (`5`) seeds. The selected rule paints the clipped Chebyshev-radius-one neighborhood of every seed blue (`1`), so each seed becomes a centered 3×3 block and overlapping blocks merge; all remaining output cells are black (`0`).

Version 3.0.0 uses a four-example deterministic curriculum. Every window contains:

1. a public-style lattice-aligned anchor;
2. an interior off-lattice counterexample to “fill the containing 3×3 macrocell”;
3. an edge seed that demonstrates clipping; and
4. an interior pair whose output halos overlap and merge.

Half of ordinary draws retain the exact canonical `(9, 9, 2-color)` profile. The other half provide controlled dimension extrapolation within `7..15`, while keeping the canonical `0/5` palette, singleton-object grammar, and three-or-four-seed default count. Exact overrides are limited to observable `grid_h`, `grid_w`, and `n_seeds`; unknown keys fail loudly.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
