# Working notes: 866b956f2402

## Review assignment review-25d55b97019872c3

Final generator 2.2.0 SHA-256: bd98b7da7022baec112397ebe048fb34b09625d9665f8967a4ff0fe98bab80b1. Racket unchanged: 7cf1bdb14040.

Repaired weak validation, inert axes, narrow support and reproducible lesson ambiguity. The normal schedule is canonical/A/B; five demonstrations plus one query span two copies of every profile. Feature allocation and capacity strata are seed-level choices; geometry varies per draw. Canonical anchors provide repeated border and independent-adjacent-cell evidence. Long stacks repeat [a,c,b] for a<b<c to refute adaptive per-segment color sorting.

Validation: final public battery 12/12; focused tests 93/93; 300 lessons, 1,800 required rotations and 1,800 unique inputs without ambiguity or execution/scoring errors against 25 unique named rivals. Fifteen shortcuts fit all five canonical pairs. Fixed seed 0 covers nine band/start combinations and 54 rotations. Independent Racket probe covers 13 manual fixtures, five canonical pairs and 72 generated cases (90 total, 74 unique); no mismatch. Exact source-bound reports and commands are in the returned checks/ evidence.

Preserved intermediate counterexamples: six border failures, rigid-run lesson, six adaptive-sort failures and frozen manual Racket witnesses. The adaptive rival caused 107 singleton-error lessons / 18 production ambiguities on v2.1's retained 300-lesson census; the final independent rescore finds zero and exactly two refutations per lesson. These are intentional diagnostic rivals, not invented failed solves.

The validator excludes whole-grid no-wall, wall-only, all-zero and no-motion teaching examples, while the probe retains their lawful Racket labels. Retired axes now fail explicitly; dimensions do not coerce booleans/strings/floats. This is an intentional breaking change from v1.1.1.

Limits: finite named-bank agreement is not universal uniqueness. Partially filled sampled segments have an empty bottom; longer stacks are confined to the special column above a bottom wall. Broader transfer is unmeasured. The independent review examined v2.1 source and the exact v2.2 delta; runtime verification was performed by root.

Reusable tools: workspace/probe_semantics.py obtains public reference labels in batches of at most 64 and checks actual declared rivals/witnesses; workspace/probe_independent_rivals.py rescores retained labels, including full-census error vectors, without extra Racket calls. Tests use reviewer_support.find_root/canonical_pairs for portable layouts. See the task workspace implementation plan and the return's REVIEW.md, DECISIONS.md and RESULTS.json.
## Current reviewer considerations

Source SHA-256: `bd98b7da7022baec112397ebe048fb34b09625d9665f8967a4ff0fe98bab80b1`.

# Decisions: 866b956f2402

## D1 — Keep the reference and repair the teacher

All five canonical outputs agree with order-preserving gravity in independent color-8-delimited column segments. The original defects were sampling, controls and validation. The Racket authority and rule hash 7cf1bdb14040 are unchanged. A Python semantic model is used for diagnostics and witnesses only; public generation and all retained reference checks use Racket. Frozen manual fixtures check broad rule inputs, including some intentionally excluded from teaching.

## D2 — Use an explicit teaching subset

The validator admits rectangular integer ARC grids with background, at least one wall, at least two pebbles and an observable move. It rejects malformed values and no-op lessons. A populated wall-free column is permitted alongside walls elsewhere. Whole-grid no-wall, all-zero, wall-only and already-settled fixtures still have lawful reference outputs; their rejection is a teaching choice. Treating every Racket-lawful grid as a mandatory generator example would obscure that distinction.

## D3 — Retire ineffective controls in a breaking version

Keeping ignored controls would preserve misleading promises. The repair exposes only grid_h, grid_w and canonical/contrast texture. Explicit dimensions are exact across easy/medium/hard, integers do not coerce booleans, floats or strings, and unknown or retired keys fail. Negative textures remain named diagnostic fixtures rather than normal helpful texture values. Their shapes still respect supplied dimensions.

## D4 — Preserve observed anchors without freezing the whole distribution

Canonical anchors retain one of five observed shapes, three occupied columns, six pebble colors excluding 1 (eight total grid values including 0 and 8), one or two internal walls per column and at most two pebbles per segment. The pebble universe across canonical examples is {2,3,4,5,6,7,9}; it is not eight movable colors in each grid. Complementary extension profiles introduce color 1, populated wall-free columns, longer stacks, more walls and more columns. Defaults vary dimensions by difficulty; shape controls permit explicit boundary probes.

## D5 — Repeat informative profiles within the actual lesson

Default lessons have five demonstrations and one query, assembled as six consecutive draws of canonical/A/B. Every starting residue contains each profile twice. Features and threshold counts are assigned at seed level, while layout and palette are drawn per example. Four pairs can contain only one example of a critical feature; the retained intentional shorter-lesson probe shows the wall-free rival fitting all demonstrations when that one example is the query. Five demonstrations are a sufficient requirement for this covering design, not a universal lower bound for the puzzle.

A single rich contrast carrying every feature in every lesson was rejected because it correlates color 1, wall-free behavior and other cues. Complementary seed-level allocation allows both separated and co-occurring features across seeds. A zero-error gated rival is reported as surviving the whole lesson; it is not counted as ambiguity when it also predicts the query.

## D6 — Make disagreements repeat, not just feature labels

The first repaired source passed the battery but its larger census found one production ambiguity and six rotated ambiguities against interior-only gravity. An independent rigid-horizontal-run rival also fit canonical examples and exposed singleton-error lessons. The revised canonical anchor places moving pebbles at a border and starts adjacent same-color pebbles above different stopping heights. Each six-pair lesson includes this concrete witness twice. Exact failures are retained under counterexamples/.

The final independent review then found adaptive_direction_sort: choose each segment's numerical sorting direction from its first two colors. It fits every canonical pair because no segment has more than two pebbles. The v2.1 census contained 107 singleton-error lessons, including 18 failing production queries. Merely repeating a long-stack profile did not force the random color orders to repeat its failure signature.

Version 2.2.0 makes the long prefix [a,c,b] for a<b<c. The rival chooses ascending from a<c and must change c>b; stable gravity preserves the sequence. Both long-profile copies therefore refute it. The separate [b,a] pair remains. Five locked cells realize three colors, preserving the existing two-duplicate palette-capacity budget. This avoids a rejection loop and keeps remaining geometry and color choices variable. Six frozen lessons and a bank-declaration test failed before this repair; all pass afterward.

## D7 — Require query rotations and bind every claim to its source

The production and rotated-query policies are both required. The final public census covers 300 lessons and 1,800 holdouts, with no errors or ambiguity against 25 unique named rivals. All nine combinations of period-three starts and bands at fixed seed 0 were separately enumerated (54 rotations, 18 unique inputs). This does not exhaust other seeds or arbitrary programs. The original and intermediate failures are preserved and cannot be reported as final-source successes.

The independent probe checks 13 manually derived fixtures, all five canonical pairs, 72 generated cases, every declared witness, and every actual declared shortcut/competitor. An additional independently implemented probe scores cross-wall, global-row-barrier, rigid-run and adaptive-sort alternatives using retained Racket labels. Its all-census adaptive rescore has zero singleton errors after the repair.

## D8 — Keep remaining distribution restrictions explicit

The canonical anchor makes border and adjacent-run evidence reliable, but also makes that profile recognizable. Partially filled segments exclude their bottom cell; the generated corpus does not establish behavior when floating pebbles sit above already settled pebbles. Longer-than-two stacks are currently confined to a special column above a bottom wall. These limitations are recorded rather than hidden by finite-bank passes. More general combinatorial support would be separate work with its own measured teaching contract.

## D9 — Finish the assigned lanes and build reusable evidence

The blind solve preceded authoring; the post-repair solve used final source bytes and disclosed prior exposure. Each has one genuine code revision, visible-only feedback, and unknown masked correctness. The two drawn audits are findings-only, with exact public-reference witnesses and unchanged source hashes. The task-local probe scripts batch the public 64-input API and retain exact raw responses, source hashes, commands and independently derived comparisons. No shared checker or audit generator is patched.
