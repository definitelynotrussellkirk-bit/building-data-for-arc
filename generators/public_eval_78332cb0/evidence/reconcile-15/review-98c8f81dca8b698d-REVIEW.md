# Review complete — two public-evaluation families

Both assigned parents now have general protected-Racket references, deterministic
generators, native parametric adapters, promotion contracts, focused tests,
finite-rival audits, sequential public views, source-bound preflights, and causal
witnesses. Both are reviewer-ready; owner registration, unchanged native
qualification, exact-source acceptance, and training admission remain pending.

- `public_eval_a6f40cea`: reconstruct occluded one-/two-color rectangular
  perimeters inside the largest color-3 frame. `reveal=perimeter` is canonical;
  `solid` reveals full inferred boxes. All 4 official labels pass. The released
  third training label has a contradictory 9/8 checker phase, retained by a
  narrow documented corner fallback that generated examples never exercise.
- `public_eval_78332cb0`: recover the unique complete connector chain among
  separator-delimited panels. `traversal=forward` is canonical; `reverse`
  reverses the chain and rotates every panel 180 degrees. All 5 official labels
  pass. The implementation correctly handles repeated local connector values by
  solving the complete chain rather than using greedy continuation.

Verification retained in `checks/`:

- 31/31 focused task tests passed.
- Both current-source authoring preflights passed.
- 1,280 finite-rival/count episodes and 10,240 pair exposures passed across 64
  seeds per target; no retained query-changing rival survived two demonstrations.
- 80 additional generated labels and 4 causal labels passed protected Racket.
- 32/32 one-query public files passed independent exact-byte/schema/privacy checks.
- Both causal witnesses returned `reviewer_replayed`; their counterfactuals change
  19 cells (`a6f40cea`) and 29 cells (`78332cb0`).
- Cross-target final review passed 554 source, boundary, prefix, privacy, maximum
  seed, and 30×30 checks.

Seed-17 stress cases are substantive: `a6f40cea` uses a 30×30 input with 155
non-background cells and 135 setting-dependent output cells; `78332cb0` uses a
30×30 input with 79 non-background cells and 72 setting-dependent output cells.
Finite rivals and bounded seeds do not prove universal uniqueness. Final review
was an author self-review rather than an independent reviewer pass.
