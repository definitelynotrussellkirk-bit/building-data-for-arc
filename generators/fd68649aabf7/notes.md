# Current decisions: fd68649aabf7

## Rule and lawful manifold

Selected sampler version 2.2.0 pins the unchanged canonical Racket authority
`f4e553d13f24`. Each monochrome four-connected body is recolored to the top-row
marker nearest its horizontal bounding-box center; exact ties choose the smaller
marker column. Markers and background persist. The sampler uses zero background,
an empty row 1, 2..6 distinct-color top markers, and 1..10 bodies whose colors
are disjoint from all marker colors. Same-color diagonal contacts are lawful.
The rule's temporary clean pass would leave marker-colored bodies unchanged in
the output; excluding those bodies is a sampler choice, not erasure semantics.

## Distribution choices and reversals

- Prior placement treated row 1 as occupied, accidentally excluding row-2 bodies.
  Reserve the coordinate domain instead, and place body seeds in rows 2 onward.
- Prior attempts could drop requested bodies. Reserve every nonadjacent seed
  before optional shape growth. Sizes may stop short, but component counts do
  not. Even 7x9 with six markers and ten bodies is supported.
- Keep four exact integer controls: grid_h 7..20, grid_w 9..24, n_markers 2..6,
  n_blobs 1..10. Their full domains apply in every difficulty. Unknown keys,
  booleans, fractional values and numeric strings now fail explicitly; None
  keeps the ordinary default. Retired palette_kind, palette_size,
  n_distinct_colors, texture, position_bias and density were unimplemented or
  constant controls and now fail as unknown instead of silently doing nothing.
- The prior equidistant fixture had center 5.5 between markers 2 and 8 and was
  not a tie. Genuine ties are lawful positive teaching cases, not degenerates.
  No-marker errors and no-body identity fixtures are outside this sampler.
- Ordinary indices modulo 3 use [canonical, joint_a, joint_b]. Canonical slots
  have randomized bodies/palettes on 9x12..14, with three markers and three body
  colors. Other slots retain difficulty-dependent dimensions/counts and a small
  two-body witness. joint_a and joint_b share one distribution; separate names
  identify schedule residues, not different concepts.

## Teaching contract

All eight rivals in SEMANTIC_RIVALS fit all four labeled canonical pairs:
centroid, left edge, right edge, floored bbox, right tie, per-pixel assignment,
body scan rank, and eight-connectivity. The saved
`counterexamples/joint_witness.json` is actually Racket-labelled and refutes all
eight. Its two same-color bodies touch only diagonally; one selects the right
marker, the other's bbox ties left while its centroid lies to the right.

Three consecutive default demonstrations contain two joint witnesses; four
consecutive pairs contain at least two, so any single query holdout leaves one.
Generation rejections and duplicate skipping could disturb this argument, so
the review also checked the actual materializer: 300 lessons, 1,200 unique inputs
and 1,200 query rotations, no ambiguity against the eight declared rivals.
The required-rotation semantic gate passed. These are finite declared-rival
measurements, not unrestricted identifiability or training admission.

## Known limits and reusable verification

Two thirds of ordinary draws deliberately share a translated witness scaffold.
Palette permutations, placements, modest motif variations, and random filler
bodies vary; the canonical slot supplies a separate broad body distribution.
Unseen shape-specific shortcuts remain untested. One-body overrides omit the
two-body witness, so arbitrary override lessons need their own teaching check.
Difficulty controls sampling preferences, not whether a lawful canonical input
is accepted. The selected rule still has a broader domain than this sampler.

`tests/test_generator.py` covers exact counts from pixels, canonical acceptance,
malformed inputs, reference execution, and all three cyclic starts/all query
holdouts. `workspace/check_teaching_contrast.py` shows why canonical correctness
alone does not identify the rule, using the saved reference-labelled query.
No current review_index.json or earlier repair was present for this target;
the original rationale for its decorative controls was unknown.
## Current reviewer considerations

Source SHA-256: `43366acb97d32b73f1e1279301d991749f30c97caa9a4929c6801b26a157f7e8`.

# Repair decisions — fd68649aabf7

Assignment `review-5b3c0730e794b9be` remained fixed. Baseline generator SHA-256
`6f880dd19120ec6114990ff49404e4ac53a908c3ce2a5ef310dc0f9ddd5d8cfe`;
final SHA-256 `43366acb97d32b73f1e1279301d991749f30c97caa9a4929c6801b26a157f7e8`.
No prior selected-task review index was present and the original notes were a
placeholder. Historical rationales are unknown unless source comments below
make them explicit. No rule or audit-target source was changed.

## D1 — preserve the Racket authority

The actual rule uses same-color orthogonal components from a temporary grid
with marker colors removed, then recolors the original grid. Its nearest-marker
distance uses the exact horizontal bbox center; equal distances choose the
smaller marker column. The canonical rule and four labels agree, so rewriting
the rule would change the task without justification. Pin `f4e553d13f24` and
improve inputs instead. Python predictions are diagnostics/rivals; reference
labels still come from Racket.

The old comment saying a marker-colored body would be erased was inaccurate:
the clean pass affects extraction, while the output starts with the original
grid. We retain disjoint body/marker palettes because they make recoloring
observable. Allowing marker-colored inert bodies is a lawful broader-domain
extension, but would require additional teaching analysis and is out of scope.

## D2 — exact controls and type boundaries

Retain full declared domains: rows 7..20, columns 9..24, markers 2..6, bodies
1..10. A requested integer applies in every difficulty, while ordinary
difficulty preferences can stay narrower. The 69,480-draw override matrix and
independent pixel-count regressions verify observable behavior.

Rejected alternatives: clamping counts, treating unknown names as no-ops, or
retaining decorative axes with untestable bookkeeping. Remove palette_kind,
palette_size, n_distinct_colors, texture, position_bias and density from AXES
and reject them explicitly. This is a caller-visible cleanup of unsupported
controls; callers using those names must update. Preserve None as the existing
no-override convention, but reject strings, floats and booleans as integers.

## D3 — constructive component placement

The old `used` set included all of row 1. `grow_blob` also refused adjacency to
used cells, unintentionally making row 2 inaccessible (0/150 diagnostic draws,
despite canonical row-2 support). Candidate coordinates now begin at row 2.

Reserve all required component seeds before growing any filler. A checkerboard
provides an orthogonally independent set after excluding motif cells and their
neighbors. Grow each reserved seed toward a small random size, stopping when
space runs out. Exact component count is the contract; an independently
advertised shape-size control does not exist. Minimum-grid high-count cases
can therefore include singletons, which are lawful under the same rule.

Rejected alternatives: increasing retry counts, silently dropping bodies, or
declaring broad incompatibilities that are geometrically unnecessary. The
7x9 / six-marker / ten-body case passes. The independent source review checked
all 28 minimum-grid motif/addition positions with capacity for eight remaining
bodies, plus 192 predetermined joint draws at selected dimensions/extremes.
This is finite evidence; the reservation argument supplies the construction.

## D4 — canonical profile and broad ordinary support

Every third default draw has 9 rows, 12/13/14 columns, three markers and three
independently colored bodies. Positions, palettes and grown shapes vary; no
canonical grid is copied. This maintains six nonzero colors plus background,
restoring exact canonical-profile support in every difficulty. Measured hits
were 22/60 after versus 0/60 before, split 7/20 easy, 6/20 medium, 9/20 hard.

The other slots retain difficulty-dependent sizes, marker counts and body
counts. Exact overrides take priority over both profile and teaching defaults.
Self-check is independent of difficulty; a lawful canonical three-body grid is
not invalid merely because the caller labels it hard. The strict hook validates
the selected manifold, not similarity by an arbitrary color/shape statistic.

## D5 — task-specific witnesses and lesson assembly

All eight declared rivals fit all four canonical pairs: centroid, left edge,
right edge, floored bbox center, right ties, per-pixel nearest, scan-rank
assignment, and eight-connected bodies. In a compact witness, active markers
lie at L and L+2. A right-assigned half-center domino is scanned before an
asymmetric body whose bbox ties left but whose centroid lies right. The bodies
share a color and touch diagonally only. Actual Racket execution on the saved
fixture confirms all eight distinctions.

Translate the motif, permute palettes, add legal marker positions outside its
interior interval, vary middle-column cells and upper domino cells, and grow
independent fillers. Do not randomly reflect a left-tie witness: that can make
centroid agree with the target and erase the intended distinction. No new task
rule is composed into the reference transformation.

Default period is three: [canonical, joint_a, joint_b]. The two joint names
identify residues of the same distribution, not separate pedagogical concepts.
Three consecutive demos contain two joint examples. Any four consecutive
materialized pairs contain at least two, so holding one out leaves a complete
witness. EXAMPLES_NEEDED remains 3; raising it to five would consume more
training context without a demonstrated need for this rival set.

The actual production sampler was checked for 100 lessons per band with all
four query holdouts. Results: 300/300 materialized, zero ambiguity/errors/warnings,
1,200 unique inputs, 1,200 successful rotations. Accepted indices and input
hashes are retained, with no rejection logs. The required-rotation semantic
gate also passed. The task tests exercise all three consecutive schedule starts
at one separate seed, avoiding an inference from only sample-index zero.

## D6 — limits, failed paths, and what was not claimed

Two-thirds witness scaffolding is intentionally strong teaching support and a
distribution restriction. Undeclared shape-specific shortcuts may remain. We
do not claim universal rule identification, human-level generalization, a
Qwen training improvement, or automatic training admission. One-body overrides
cannot contain the two-body witness; arbitrary override lessons must be checked
as actual assembled lessons, not covered by the default schedule argument.

Baseline battery failures and both pre-repair red test runs are retained. The
first candidate passed its 45-case focused suite; additional canonical-rival,
minimal-fixture and short-grid checks bring the final suite to 48. The isolated
task-test preflight initially failed because pytest was only in user-site;
provisioning an independent venv copy resolved it while keeping isolation on.
A wrapper launch with a relative payload interpreter also failed because the
wrapper changes cwd to repo; rerunning with the absolute interpreter succeeded.
The failed results were not relabeled as generator failures or deleted.

The blind task was completed before any task source exposure. The post-repair
episode was prepared from final generator bytes, solved without reopening
reference material, and honestly marked as having prior exposure. Both first
actual attempts passed their three visible examples; private-query correctness
remains unknown. No failure was manufactured for a training pair.

Both audits remain findings only. Their current source hashes and actual
reference counterexamples are retained; acceptance of the selected repair
does not resolve them. Reviewer checks are reported evidence, pending normal
maintainer intake; source snapshots and a finite check are not model approval.
