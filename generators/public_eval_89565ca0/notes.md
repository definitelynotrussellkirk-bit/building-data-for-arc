# Occluded partitions: current authoring decisions

## General rule and explicit extension

Recover each structural color's rectangular wall network, count its enclosed
four-connected rooms, and render one row of that color repeated by its room
count. Pad shorter rows with the scattered noise color. The canonical order is
ascending room count. Every supplied training label and test gold will be
executed through the authored Racket reference.

The one original equal-count pair agrees with both numeric color order and
leftmost position. This does not uniquely specify a tie rule. The reviewer
chooses the spatial extension leftmost bounding box, then topmost, then color,
and will teach it with examples that contradict numeric and topmost-only order.
The alternative setting sorts counts descending while preserving tie direction.

## Design and implementation plan

The packet's task notes and check receipts own the plan and progress; no Git
repository is present in this fresh isolated extraction.

- [x] Add focused tests for original labels, partial dividers, occlusion repair,
  noise identification, tie direction, types and malformed grammar before code.
- [x] Author the general Racket reference and a portable input generator with
  input analysis/self-check. Identify supported axes by adjacent own-color
  pixels plus bounding-box sides. The unique color with off-axis pixels is
  noise. Restore elementary wall intervals from their own-color interior
  witnesses; force the outer perimeter and count regions. Do not borrow foreign
  crossing walls or fill an entire partial divider's row.
- [x] Add deterministic matched-input banks and a thin native adapter for
  `sort_order=ascending|descending`, exact canonical default, 2..6 demos and
  1..4 independently prefixed queries. Use two distinguishing teaching scenes,
  four novel queries, palette/topology/geometry variation and a substantive
  30x30 input with a 30-room partition.
- [x] Execute current-source shortcut audits and maximum-count/seed boundaries;
  repair concrete demo-fitting/query-conflicting rules before preflight.
- [x] Run public authoring preflight, protected causal replay and verified
  single-query projections with negative cases. Record both reviewer-ready
  targets, reports and the compact source delta for owner integration.

Reconstruction by supported elementary intervals is preferred to simple line
counts or full-grid products because the originals contain T-junctions. A
nonzero-chain bridge can borrow another object's crossing wall and invent rooms.
The reconstruction must preserve each genuine axis and one own-color interior
witness per elementary wall interval after compositing. Consecutive axes are
separated by at least two cells. Restored walls contain no raw zeros: all missing
original wall pixels are nonzero occlusions. Generated room counts remain 1..30.

## Sequential dependency and review focus

A reconstructs the current input's wall networks and derives each object's
room count and location. B sorts those records and renders the padded rows.
Damaged-wall omission or borrowed foreign walls can change the counts and hence
both order and width. This is input-dependent reconstruction and ranking,
without a claim of iterative simulation.

Review partial divider topology, overlapping foreign walls, erased intervals,
unique noise detection, equal-count ties and strict one-query public visibility.
The new sources are unapproved authoring work. Owner registration, source review,
native qualification and fresh acceptance remain separate; training is not admitted.

## Current construction and retained review findings

The independent Racket implementation passed all four supplied original labels
and ten hand-fixture labels: partial T junctions, primary and secondary spatial
ties, foreign-wall crossings, and a 30-room partition, each in both orderings.
The Python family/parser tests passed 23 focused checks before sampler completion.

The first two generated lessons have room-count multisets [1,3,3] and [2,4,4].
The first contrasts leftmost order with both numeric and topmost order. A tiny
one-room frame has at most seven visible pixels, fewer than the noise budget,
so choosing the rarest nonzero color cannot identify noise. The second includes
equal-left ties and different four-room topologies: a partial partition and a
full two-by-two crossing. The axes-sum rule H+V-3 fits all three original training
labels but fails the supplied test, undercounting its five- and six-room objects.
The full crossing distinguishes that rule from actual enclosed-room counting.

Review found two construction defects before source freeze. The largest scene
could paint its 30-room core last, making only smaller objects suffer overlap;
the core is now below the smaller frames and must contain a foreign occlusion.
The foreign-chain teaching regression originally scanned arbitrary rows, which
missed a mismatch with the rival's supported-axis rows. Tightening the test
produced three retained failures. Moving the crossing frame to (5,8,24,28) fills
the absent horizontal interval at row 5, columns 9 through 14, while preserving
own-color witnesses on both genuine vertical dividers.

Noise uses a complete validated bank of 32 edits before selecting the requested
8..32 prefix. Each prefix preserves latent wall sets, bounding boxes and room
counts, so changing the noise override does not select a different geometry.
The sampler draws two or three structural colors per generated scene; the parser
admits two through eight. Query canvases are 12x15, 19x23, 26x29 and 30x30. The
largest includes a five-by-six room partition with 255 true wall pixels. These
are sampled profiles, not claims of complete coverage of the broader grammar.

## Final reviewer evidence

The frozen build passed 103 focused tests, the actual static linter with no
errors or warnings, and 152 protected rival comparisons across seeds 0,17,43 and
2**63-1 in both settings. All tested rivals were refuted by the two teaching
examples; no generated query conflict or execution error remained. The native
suite contributes 88 comparisons and the independent suite 64, with exact
first-disagreement witnesses in checks/public_eval_89565ca0/independent-audit/.
This is bounded evidence, not universal identification.

Twenty protected maximum-seed labels cover six demos and four queries per
setting. The largest input has 344 nonzero cells on a 30x30 canvas, a true
30-room partition, and a 3x30 output. Public authoring preflight passed all four
seed/setting jobs and all four supplied original labels, binding 154 source
files. Two protected wrong-intermediate cases were constructed and replayed.
Sixteen single-query public views verify exact answer pairing, equal first turns
for one/four-query exports, private-field/future-query invariance and full-bank
shuffle-before-prefix; four deliberate corruptions were rejected.

Historical RED and intermediate failures remain under checks/ with their actual
command receipts. The final source is reviewer-ready. Owner registration, native
qualification and fresh acceptance remain pending; training is not admitted.
