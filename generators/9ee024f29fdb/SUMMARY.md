# 9ee024f29fdb

A zero-based 4-spaced coordinate lattice is always cleared: output 0 whenever
`r % 4 == 0` or `c % 4 == 0`. Off the lattice, input color 8 is erased to 0 and
every other value is painted red (2).

Generator version `3.0.0` alternates a canonical `{0,8}` clean-lattice profile
with a joint counterexample profile containing interior decoys and nonzero
values on every periodic row and column. Three demonstrations are required so
every cyclic query rotation retains at least one counterexample. Exact public
axes are dimensions, interior decoy-palette size, and lattice-noise mode;
density and geometric layout are diagnostic construction controls.

Kind: `per_puzzle`. Canonical rule hash: `82f439b3efb8`.
Approval remains catalog-derived from current source and retained evidence.

A proposed native parametric family in `workspace/parametric/` varies lattice
period `{3,4,5}` and repaint color `{2,4}` while preserving `(4,2)` as the exact
canonical default. It supports 2–6 demonstrations and four-query episodes with
exact canonical public bytes and `challenge-<full-sha256>.json` identities. The
current manifest is `de2fe9fd33c07ce6469ed302229713966cbeb0beec5525c5e15e7880b3bdb14c`.
Its Racket-backed evidence is freshly qualified; it is not accepted or admitted
to training.
