# 576426a573af

Preserve every original non-zero cell. For each zero cell, copy the value from
its vertical mirror when that mirror is non-zero. Different non-zero values in
a mirror pair therefore remain in place; the reflected value never overwrites
an occupied destination.

The version 2.0.0 generator uses a deterministic four-role curriculum. Every
four consecutive sample indices contain: a canonical bottom-anchored scene, a
top-source scene, a bidirectional singleton scene, and a conflicting non-zero
mirror pair. The public override surface is limited to exact `grid_h`,
`grid_w`, and `fg_palette_size` controls.

Kind: `per_puzzle`. Selected version: `2.0.0`.
Canonical rule hash: `892d64eecd2e`.
Approval is derived by the catalog from current code and retained evidence.
