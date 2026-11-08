# Working notes: 864b0302e2e6

## 2026-10-24 bounded control repair

The declared `missing_quad` axis was never consumed: `generate()` selected the
empty quadrant with `layout_rng.randrange(4)`. Exact overrides therefore did
nothing and invalid values were silently accepted. The generator now uses
`ctx.draw_int_strict("missing_quad", 0, 3)`, which makes all four values visible and
fail-closes on invalid types/bounds. `VERSION` is 2.1.2 because the default
seed-to-grid mapping changes when the missing-quadrant draw moves to its named
axis stream.

The prose also incorrectly described the current motif as a fixed four-cell
shape. Normal generation has used a random nonempty proper subset since 2.1.1;
the fixed `MOTIF` remains only in degenerate fixtures.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
