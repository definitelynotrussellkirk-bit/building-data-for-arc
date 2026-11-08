# Working notes: 71f7823f30a3

## Current native candidate

The approved production generator 3.0.0 and exact canonical rule remain unchanged.
The native `copy_policy` is `all`, `nearest_color` or `farthest_color`. Each
anchored row discovers its own nearest/farthest source, reads that source's
color, and reflects every source of that color, including remote sources on
the opposite side. Sources, anchors and unanchored rows are preserved.

A selects a source column from its distance to the row-local maroon anchor;
the intermediate is the color read there; B uses that color to choose which
other source cells to reflect. The qualified witness replaces only the cue
selector. Both selective policies change 12 final cells in the retained 6×15
case. This is an original-input dependency, not iterative grid simulation.

### Teaching repair and verification

The first proposed two-demo cores allowed four coherent whole-color summaries
to imitate individual-source selection: minimum/maximum exact mean distance,
minimum farthest-member distance and maximum nearest-member distance. Protected
before evidence is `checks/71f7823f30a3/review-extents/before.json`. The second
core now interleaves near and far members of the same color; its output refutes
all four without adding a demonstration. The protected after report is
`checks/71f7823f30a3/review-extents/after.json` (57 applications each, before/after).
A missing closing parenthesis in the first alternate source was separately
fixed and pinned by the native-wrapper syntax regression.

Current focused suite: 52 tests passed. The source-bound teaching report at
`checks/71f7823f30a3/native-teaching/report.json` covers two seeds, three settings,
two demonstrations and four independent queries, with 432 protected Racket
applications and independent Python parity. Only the matching-policy positive
control survives among 31 hypotheses in every episode; all 30 other hypotheses
are refuted by demonstrations. Mean comparisons use exact cross-products.
This is finite support, not universal rule identification.

`checks/71f7823f30a3/sampler-v2.json` records 144/144 successful Python requests,
160 distinct inputs and 64 distinct queries for 16 seeds across settings/counts.
All inputs and prefixes are shared across settings and count requests. These
sampling checks do not execute Racket. Native qualification executes 132 labels
for the full six-demo/four-query bank, all three settings and seeds 0/17.
Qualification and causal witness/replay are under `checks/71f7823f30a3/`.

### Support and remaining limits

Ordinary counts are three demonstrations and four queries; supported counts are
2–6 and 1–4 independently. The ten profiles span 4×7 through 30×30 and include
rectangular, tall and wide scenes. The large demo/query have 24/25 anchored rows;
seed 0 has 293/290 anchored source cells and changes 104–293/107–290 cells across
the three policies, with changes in all four quadrants. Every source has an
empty, in-bounds reflected target. Equal-distance occupied pairs, multiple
anchors per row and anchor-only rows are outside the native grammar.

The native size envelope is height 4..30, width 7..30; only documented profiles
are sampled. No size override or 90-degree rotational invariance is advertised.
Production remains height 4..10 and width 7..15. Native settings and large profiles
are separate proposals, not new production support.

`checks/tools/export_qualified.py` verified current qualification bindings and
projected three seed 0 controllers into 12 content-addressed one-query actor files.
Only the current actor file is visible; future inputs, answers, settings,
programs, seeds, manifests and directory listings remain private. Export tests
cover identical first-turn bytes with one versus four controller queries.

Both native source and evidence are reviewer-ready. Exact-source owner
acceptance remains pending; no training admission or measured learning gain is
claimed. The unchanged production tests/battery were not rerun for this
prototype-only change. No inherited production audit disposition was changed.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
