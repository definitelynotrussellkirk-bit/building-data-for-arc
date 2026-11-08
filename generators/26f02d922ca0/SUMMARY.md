# 26f02d922ca0

A zero-background grid contains one color-2 key shape and 2–4 isolated
candidate shapes in distinct colors from `{3,4,5,6}`. Candidates are read in
top-left order. The output is a `1×N` row: `8` exactly when a candidate's
normalized shape equals the key or its horizontal mirror, otherwise `0`.

Version `3.0.0` uses a deterministic four-profile curriculum:

1. canonical-scale `9×16` color-role conflicts,
2. non-prefix reading-order conflicts,
3. asymmetric mirror-only matches, and
4. variable candidate counts.

Together these profiles refute the three shortcuts that fit every canonical
demonstration—fixed colors 3/4, “first two match,” and fixed output
`[8,8,0,0]`—plus the exact-key-only rival. The generator pins canonical rule
hash `2ec8ce6b9b7f`, exposes only exact observable `grid_h`/`grid_w` overrides,
and declares the full 21-state mixed-label output codomain.

Review evidence: 16 focused tests pass; the source-bound 12-stage after battery
is all green; the semantic census reports 4/4 witnesses firing, 4/4 rival
claims verified, and 12/12 generated lessons identifiable.

Kind: `per_puzzle`. Current version: `3.0.0`.
Approval remains derived by the catalog from current code and retained evidence.
