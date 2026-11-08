# Working notes: 59d146376904

## Current decision

Retain the exact canonical rule as `summary_order=spatial`. Add one nearby native
setting, `summary_order=majority_count_desc`: A computes each quadrant's unique
most-frequent nonzero color and exact count; the intermediate is the quadrant
index ranking by count; B emits the selected colors through that ranking.

## Base repairs

- The old `grid_h`/`grid_w` controls were advertised but ignored. They are now
  strict, observable even dimensions; legacy `qh`/`qw` aliases remain supported
  and incompatible pairs are rejected.
- `self_check` previously accepted a tied-majority negative fixture. It now
  validates exact grid types, even dimensions, a unique nonzero winner in every
  quadrant, and distinct selected colors.
- The old prose incorrectly required the winner to exceed half the quadrant.
  Canonical labels only require a unique most-frequent nonzero color; source and
  summary now match that executable meaning.
- Ordinary generation now contains non-major nonzero evidence and corner cues so
  first-cell, highest-color, background-inclusive, and global-frequency shortcuts
  are not silently accepted.

## Parametric teaching and adversarial repair

The family supports 2–6 demonstrations and exactly four distinct matched-input
queries. The first two constructive demonstrations cross majority-count rank
against spatial order, nonzero density, runner-up count, majority margin, color
order, global frequency, and fixed permutations. Queries include 6×8 through
30×30 shapes, with a fully occupied 30×30 case.

Observed and repaired during review:

1. Early two-demo examples left `rank:nonzero-count-asc` and
   `rank:margin-desc` alive. The teaching profiles now cross those nuisance
   statistics explicitly.
2. Large 30×30 minority masses could exhaust the eight available non-major ARC
   colors. The allocator now raises its per-color capacity to
   `ceil(nonzero_remainder / 8)` before distribution.
3. The 64-seed audit repeatedly reparsed the canonical 2.7 MB JSONL. The exact
   canonical-program lookup is now cached and regression-tested.

The final bounded probe covers 384 episodes (64 seeds × demo counts 2/3/6 × two
settings), 43–44 named rivals per setting, all colors 1–9, nine shapes, and up to
900 nonzero cells. It found no demonstration survivor or query-changing survivor
inside the declared bank. This is finite evidence, not proof against arbitrary
programs.

## Source-bound evidence

- Inventory: `workspace/parametric/evidence/manifest.json`
- Protected authoring preflight: `checks/59d146376904/qualification/`
- Causal witness: `checks/59d146376904/causal/witness.json`
- Public projection and first-turn checks: `checks/59d146376904/preview-verify.json`
  and `checks/59d146376904/first-turn.json`
- Bounded rival report: `checks/59d146376904/adversarial/report.json`

The protected witness ranks quadrants `[0,3,1,2]` from counts
`[11,8,7,9]`. The ranked program returns `[[7,4],[9,6]]`; replacing that
intermediate with fixed spatial order returns `[[7,9],[6,4]]`.

## Remaining limits

Owner exact-source review, native qualification/acceptance, and any training
admission remain downstream. No approval or training flag was changed. The
finite rival bank does not establish unrestricted rule uniqueness, and the
causal helper verifies final protected labels rather than independently proving
the authored interpretation of the intermediate.
