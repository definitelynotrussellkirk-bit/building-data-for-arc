# Decisions

## D1 — Fix the generator taxonomy, not the canonical rule

The selected rule is correct and simple. The defect is coverage: generated
lessons couple two independent properties. Therefore the production change
adds mixed-axis profiles rather than changing `compress-grid`.

## D2 — Preserve high-level distribution contracts

The new weight vector has 20 entries per difficulty: five public profiles,
six nonuniform, three interior-merge, two fully uniform, two uniform-row, and
two uniform-column. This preserves the old 25% public share and 10% fully
uniform share while adding explicit independent-axis support.

## D3 — Give mixed cases first-class observable names

`_analyze` now reports `uniform_rows` and `uniform_cols` separately and assigns
`scene_profile` in this order: canonical public, interior merge, both uniform,
rows only, columns only, neither. This keeps override recovery exact.

## D4 — Repin provenance to selected authority

`RULE_HASH` is `0805714fcf25`, the first 12 hexadecimal characters of SHA-256
over the whitespace-normalized selected canonical program. A regression test
recomputes the pin from canonical data.

## D5 — Make task tests portable

Tests use `reviewer_support.find_root(__file__)` and `canonical_pairs`, rather
than assuming that `parents[1]` is the repository root. This is necessary in
the packet's isolated task-test runtime.

## D6 — Keep public-evaluation routing semantics separate

The marker-count/clearance mechanism inferred from `cb2d8a2c` is structurally
interesting but not a lawful extension of this compression generator. It is
recorded as a separate-family proposal rather than forced into production.

## D7 — Parameterize only bounded, testable rule choices

The prototype varies compressed axes (`both`, `rows`, `columns`) and output
orientation (`identity`, `transpose`). The canonical setting remains
`both/identity`. Demonstrations must refute every rival before queries are
emitted, and all labels come from materialized Racket programs.

## D8 — Guard the recovery artifact

Because the original 350 MB attachment exceeded the 100 MB rematerialization
limit after a workspace reset, the repair is distributed as a source-hash-
guarded patch kit. It refuses to overwrite a generator other than the exact
baseline hash `836fa3a06d55f5a6450ccf989f8187695e6f45d8ef81f0a6a384a853a73409af`
unless explicitly forced.
