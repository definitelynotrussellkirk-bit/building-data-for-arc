# Working notes: e6cf1120a17d

## 2026-10-26 repair and parametric build

- Repaired the prose/source mismatch: the canonical executable clears the four
  inset marker cells to `0`; it does not restore rectangle color there.
- Extended legal ordinary bounds to 30×30 and rectangle dimensions to `h-2` /
  `w-2`, preserving the required one-cell outer margin.
- Added an exact-default `diagonal | min_color_turn` native family. The latter
  uses the input-dependent minimum marker quadrant to choose a clockwise or
  counterclockwise destination permutation.
- The two-demo curriculum includes both turn branches. Protected-Racket tests,
  authoring preflight, causal wrong-turn replay, finite-rival self-review, and
  single-query public projection all pass.
- The retained historical review index predates this repair and remains
  unchanged; owner intake must reconcile it against the exact patched bytes.
- Owner source review, native qualification/acceptance, and training admission
  remain pending.

Current incoming extension: `workspace/proposals/review-691233545f793e4f/decision.json` retains the maximum-marker-to-top-left routing proposal and its source-bound evidence. The accepted minimum-marker family remains selected; this complementary proposal awaits grouped reconciliation and has no separate acceptance or training admission.
