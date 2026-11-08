# Working notes: a86a630485ac

## 2026-10-25 review-2f9d5f677fb14011 — native parametric build

Built `workspace/parametric/native_family.py`, a thin native adapter, promotion
contract, exact canonical program copy, source inventory, focused tests and a
protected-Racket teaching audit. Four settings combine `axis={lr,ud}` with
`keep_policy={all,largest_eligible}`. The canonical `lr/all` setting returns the
exact authority text. Production version **3.2.0**, generator SHA-256
`6283ff85053f392b32c642bd1977573ca43489b4a7c804d0d576b0bed394580e`, and rule hash
`3cb323ae99fd` are unchanged. Final native source SHA-256 is
`7050de820b6a98a96ea8d43d8b00e578fefd460e9e77c214fbfde8f2d1dcfcc1`.

The alternative composes symmetry eligibility with ranking by occupied-cell
count within the eligible set; all maximum ties survive. A larger asymmetric
component exposes the wrong order of ranking globally before filtering. Native
`review_witness` replays one exact binding intervention on each axis: replace
`(ranked eligible)` with `(ranked objs)`, preserving classification and painting.
This changes the answer in both qualified cases. The dependency is conditional
selection, not iterative simulation; intermediate descriptions are authored
metadata and the executed outputs provide the finite evidence.

Construction supports 2–6 demos and 1–4 queries, defaults to 3/4, constructs the
full bank before slicing, and uses separate deterministic streams for input
geometry and query order. The two core demos distinguish axis, ties, occupied
size versus box area, and filter/rank order. Additional profiles reach substantive
30×30 inputs with nine objects and dense retained winners in all four quadrants.
The first implementation exposed two slot-fit mistakes (6×8 gaps and a 23×27
query); retained red tests led to zero-gap small slots and a 23×29 query.

Self-review then strengthened two shortcuts even though the initial surviving
rivals agreed on the bounded queries. The asymmetric eight-cell distractor now
has palindromic row/column count projections, so counting cannot replace bitmap
reflection. Its same-color diagonal chain reaches a largest LR winner, making
four- versus eight-connectivity observable under every setting. Both changes
retain the two-demo minimum. Red/green receipts and the initial audit are kept.

Final evidence under `checks/a86a630485ac/`: **48 focused native/audit tests**;
**192/192** sampler/count/prefix requests across 16 seeds; **156 rival/episode
comparisons, all demo-refuted**, using 66 exact programs and 328 distinct
protected-Racket executions; and all 80 intended labels from the full ten-input
banks checked. Native qualification covers four settings, seeds 0/17, six demos
and four queries (**224 evaluations**). Causal construction/replay contains two
cases. Native public export/verification yields eight private episodes and
**32** exact one-query public files. Full source inventory is
`workspace/parametric/evidence/manifest.json`.

One raw whole-test-directory collection attempt failed because the legacy
`puzzle_generators.per_puzzle` namespace is absent outside the staged runner;
its exit-2 receipt is retained. The explicit native/audit test command passes.
The unchanged production battery was not rerun and is not certified here.
Sampling is a finite constructive shape/profile bank; arbitrary polyominoes,
all legal dimensions, universal rule uniqueness and training gains are unproved.
Next owner action: integrate the exact native source, qualify and freshly accept
both assigned builds. This return is reviewer-ready; owner acceptance remains
pending and no training data or activation is admitted.

## 2026-10-04 review-cd76f14ab38151f7

The selected 3.1.0 baseline passed all 12 inherited battery stages, but a direct
distribution probe found a systematic geometry shortcut. Across 320 ordinary
scenes per band, `keep objects whose bounding-box width is at least its height`
matched 320/320 easy scenes, 161/320 medium scenes, and 46/320 hard scenes. No
easy or medium scene contained a kept/erased pair matched on cell count *and*
bounding-box dimensions, and every generated object was at most 3x3.

Version 3.2.0 replaces the ordinary orientation witnesses with paired LR-only
and UD-only objects sharing exact size and bounding box. Even sample indexes use
a 3x3 five-cell pair; odd indexes use a connected 3x4 eight-cell pair. Canonical
anchors remain unchanged on the existing one-in-five schedule. A named
`keep_wide_or_square_objects` rival and `aspect_ratio_shortcut_rebutted` witness
now participate in semantic and lesson checks. The Racket authority and
`RULE_HASH` are unchanged.

The task-local canonical test also used a guessed relative ledger path that
failed in the portable task-test runtime. It now uses
`reviewer_support.canonical_pairs(..., root=find_root(__file__))`.

Final evidence: `checks/geometry-probe.json` measures 320/320 matched-role
geometry scenes and 0/320 aspect-rival matches in each band; width-4 objects
occur in every band. `checks/lesson-census.json` materialized 100 lessons per
band (300 total, 1,200 unique inputs) with zero declared ambiguities and refuted
the new rival in every lesson. The finite curriculum still tops out at 3x4;
this is improved support, not proof over every connected bitmap accepted by the
authority.
## Current reviewer considerations

Source SHA-256: `6283ff85053f392b32c642bd1977573ca43489b4a7c804d0d576b0bed394580e`.

# Decisions for a86a630485ac

## G1 — Rebut the bounding-box aspect-ratio shortcut

**Baseline finding.** The inherited 3.1.0 source was internally valid and passed
all 12 battery stages, but its ordinary easy scenes always paired a 2x3
LR-symmetric T with a 3x2 UD-symmetric T. Consequently the rule “keep objects
whose bounding box is at least as wide as it is tall” matched 320/320 sampled
easy scenes. It also matched 161/320 medium and 46/320 hard scenes. The baseline
never generated an object wider than three cells. These are measured results
from a 40-seed, eight-non-anchor-index probe per band; the final reusable probe
is `repo/generators/a86a630485ac/workspace/geometry_probe.py`.

**Chosen repair.** Every ordinary scene now starts from one of two paired role
families:

- a five-cell 3x3 pair: an LR-only vertical T to keep and a UD-only horizontal T
  to erase;
- an eight-cell connected 3x4 pair: one LR-only and one UD-only object.

Within each pair, the positive and negative objects have the same cell count,
height, width, occupied-area ratio, and coarse placement capacity. LR/UD flips
still vary orientation without changing the semantic label. Even non-anchor
sample indexes select the 3x3 pair and odd indexes select the 3x4 pair, making
the wider support deterministic and replayable rather than probabilistic.

**Why 3x4 rather than arbitrary 4x4 shapes.** Every declared dimension/profile
override must remain feasible, including four-object scenes on a 6x8 grid. A
3x4 role pair fits the smallest 3x4 quadrant exactly. Height-four objects would
fail some legal override layouts unless placement and axis contracts were also
redesigned. The selected change expands morphology while preserving every
advertised override.

**Rejected alternatives.** Merely adding more 2x3 and 3x2 prototypes would leave
the aspect-ratio shortcut intact. Quarter-turning arbitrary shapes was rejected
because a 90-degree rotation can exchange LR and UD symmetry and therefore
change the label. Removing the exact canonical anchors was rejected because it
would sever the generated curriculum from the empirical task manifold. A fully
procedural polyomino enumerator was deferred: it adds placement and
identifiability risk without being needed to close the measured shortcut.

## G1 — Semantic contract and generated-quality enforcement

A named rival, `keep_wide_or_square_objects`, now selects objects with
`bbox_w >= bbox_h`. The paired witness requires both a matched
`(cell_count, bbox_h, bbox_w)` positive/negative geometry and a disagreement
between that rival and the intended output. It is included in
`SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and
`WITNESS_RIVALS`. Generation also fails immediately if an ordinary scene lacks
the matched geometry or still agrees with the rival.

The post-repair probe measured 320/320 matched-geometry scenes and 0/320
aspect-rival matches in each band. Width-four objects appeared in all bands.
The source-bound census materialized 100 lessons per band, 400 unique inputs per
band, with zero ambiguity/errors and the aspect rival refuted in all 300
lessons. Evidence: `checks/geometry-probe.json` and
`checks/lesson-census.json`.

## G2 — Make canonical task tests portable

The inherited `_canonical_pairs()` test guessed
`ROOT / "data/canonical/puzzles.jsonl"`. The official portable task-test stage
copies tests into a different tree, where that path does not exist; the TDD red
run therefore produced one unrelated `FileNotFoundError` in addition to the two
intended new failures. The test now imports `canonical_pairs` and `find_root`
from `reviewer_support`, as documented by the packet. The same official stage
then passed 122/122 tests. Evidence: `checks/tdd-red/` and
`checks/tdd-green-1/`.

## Canonical anchors and authority

The existing `sample_index % 5 == 0` canonical schedule, strict profile keys,
dimensions, palettes, and role-tagged canonical morphologies are unchanged.
The Racket program, canonical ledger, and `RULE_HASH = "3cb323ae99fd"` are
unchanged. Only the Python teaching distribution, semantic rivals/witnesses,
task tests, and documentation changed. The after battery's rule-smoke and
authority-sync stages are green.

## Remaining limitation

The ordinary curriculum is still a finite bank and currently reaches 3x4, not
every connected shape that the mathematical authority can classify. The Python
mirror remains broader than the teaching distribution only within its declared
3x4 structural domain. Future expansion should retain exact positive/negative
geometry matching, legal override fit, cyclic lesson checks, and the one-in-five
canonical anchors rather than simply adding unpaired shapes.
