# 891a82451a8a

Version `3.0.0` generates a `5..18 × 5..18` rectangular grid with a unique nonzero modal background and exactly one seed. The seed color comes from the authoritative cycle:

`0 → 5 → 2 → 8 → 9 → 6 → 1 → 3 → 4 → 0`

The output preserves the input dimensions. At cell `(r, c)`, let `d` be the Manhattan distance from the seed and let `p` be the seed color's cycle index. The output is `cycle[(p + d) mod 9]`.

The exact observable controls are `grid_h`, `grid_w`, `bg_color`, `seed_color`, and `seed_region` (`corner`, `edge`, `center`, `interior`). Defaults cover all legal sizes, all nonzero backgrounds, every cycle phase, and every region, with a periodic `8 × 8` two-color branch in every difficulty band. Background `0` is intentionally excluded because the selected authoritative Racket runtime's `mode` primitive ignores zero-valued cells.

The generator pins canonical rule hash `635140e0e1b3`, includes an independent Python diagnostic mirror, declares executable semantic rivals and witnesses, and uses two demonstrations per lesson. Task-local tests cover canonical ownership, exact overrides, deterministic sampling, profile support, Racket-domain restrictions, distribution breadth, declared rivals, and all tested cyclic starts/query rotations.
