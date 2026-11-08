# Working notes: f7672a367745

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Pending external audit evidence

Reported no issue in a finite 14-test/300-lesson/1,200-rotation scope; overlapping and 2x2 rectangles remain excluded sampler limits. Audited source hash matches current bytes. Original packet/draw remains unverified; no audit resolution is inferred. Findings and exact witnesses: `counterexamples/unverified-d21992d34c6ba325-381c906d43d2/`; current status is in `evidence/review_index.json`.

## Native parametric return — review-1773634893c78c7e

Built a separate native family with `fill_policy=outline|largest|smallest`.
The default returns the exact canonical program bytes; the alternatives fill
all rectangles tied for the largest/smallest inclusive area and outline others.
A reconstructs same-color two-marker bounding boxes and their areas; B uses the
input-derived ranking to choose which interiors to fill. Scores come from the
original input, and ascending numeric-color painting preserves canonical
behavior, including overlaps, lines, ignored non-pair colors and blank grids.
Production v3.0.0 and canonical authority are unchanged.

The sampler constructs matched six-demo/four-query banks before slicing, with
independent supported counts of 3–6 demos and 1–4 queries, strict seeds, local RNG
and 64 bounded duplicate attempts. Ordinary examples use disjoint rectangles
with visible interiors. The API accepts all literal ARC grids of side 1–30,
while generated examples remain in that narrower grammar. Queries include 3×3
and 30×30; the maximum case has nine rectangles, 18 markers touching all four
boundaries, and 242/298/248 occupied output cells under outline/largest/smallest.
Input sparsity is inherent to two markers per nonzero color, not padded content.

### Observed teaching gap and checked repair

The initial first three demonstrations had at most two distinct area levels.
A complete executable rival that fills all rectangles except the opposite
extreme (and fills all when all areas tie) fitted every visible demonstration
under each ranking policy but changed 38 cells on query 2. The 16-evaluation
protected witness, exact original lessons and both programs remain in
`checks/f7672a367745/middle-gap.json`; this preserves an alternative-answer case.

D2 now contains six rectangles with areas 24, 24, 28, 32, 36, 36, retaining both
extreme ties and two intermediate levels. At seeds 0/17, only D2 changed; the
other nine bank inputs are byte-identical to their pre-repair values. The demo
count stays three. The new demonstration-only regression and executable
non-opposite/mean/median rivals prevent recurrence. All 12 such comparisons
across both settings and seeds are refuted specifically by D2.

### Final executed evidence

- `native-tests-final-r3-command.json` / `.xml`: 62 focused tests passed
  (48 adapter + 14 audit), zero failures/errors/skips. Includes all 8 D4 transforms
  for all 3 policies, independent literal labels, all 5 canonical pairs, overlap
  order, ties, ignored colors, line cases, strict API/count boundaries, matched
  prefixes and public projection.
- `audit-r1/report.json`: 6 episodes, 42 generated + 5 canonical labels,
  166/166 candidate comparisons refuted on the first 3 demos; 485 protected
  evaluations, 60 cache hits, 24 strict public files, zero failures/survivors.
- `qualification/qualification.json` and `execution.json`: native qualified,
  3 settings × 2 seeds, 3 demos/4 queries, 78 protected evaluations.
- `causal/witness.json` and `replay.json`: reviewer_replayed. Replacing only
  `(map rectangle-area boxes)` with `(map rectangle-perimeter boxes)` reverses
  scores 40/42 versus 28/26, changing 36 cells under each alternative policy.
  Input, boxes, policy, ties and paint logic are fixed.

The initial pre-implementation test correctly failed while the family module
was absent. The copied audit guard also failed because it expected four saved
canonical pairs; it was corrected to this task's five. Earlier green runs
precede the D4 addition or middle-area repair and are superseded by final-r3.
These stages and their real exit codes remain in command receipts. No production
battery or historical external audit was rerun. The prior `needs_evidence`
disposition remains unchanged because its original packet/draw provenance is
still unverified; these new scoped prototype checks do not resolve it.

MAIN is reviewer-ready, with source-bound native inventory, qualification and
causal replay. Exact-source owner acceptance after integration remains pending;
training admission is false. The finite seed/rival evidence does not establish
universal learnability or measured training gains.
