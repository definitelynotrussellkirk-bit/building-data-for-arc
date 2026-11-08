# Current decision — strand contour family

The newly authored general `reference.rkt` exactly reproduces all five supplied
training labels and both supplied test labels through protected Racket. No
original grids or answers occur in executable generation code.

Canonical: discover monochrome 8-connected components using the modal
background. A straight edge-reaching pole with a strand beside its inner endpoint
establishes the forward axis and transverse side. Among non-role components
strictly ahead, select the nearest obstacle whose leading contour is reachable
with unit transverse steps (ties: transverse displacement, then reading order).
Measure source cell count, derive the obstacle's per-axis exterior silhouette,
approach it, trace it, and turn inward diagonally after its last slice. Erase only
source components. Stop after the measured number of cells or at a canvas edge.

`strand_extent=source` is the exact canonical source. `plus_two` changes only
the budget to source count + 2. Both settings use identical inputs, independent
2–6 demonstration and 1–4 query prefixes, and a shuffled four-query private bank.
Public views carry only demonstrations and one query input; no count hint.

The first two lessons refute 12 retained alternatives: changed length policy,
identity, rectangle contour, straight ray, source retention, first-strand-only,
bounding-area length, axis-span length, four-connected source splitting, literal
zero background, fixed output color, and failure to turn after the obstacle.
Finite rejection does not prove uniqueness among arbitrary rules.

Four-scene examples deliberately reuse colors across roles. The 30x30 profile
has poles on all four boundaries, multiple irregular obstacles, and four strands;
it is not a padded single object. Tests also preserve all stationary cells,
check local paths, and apply every D4 transform plus a color permutation to all
seven supplied examples. A protected causal replay changes exact contour to its
bounding-box envelope and changes ten cells for the retained witness.

Limits: generated scenes exclude crossing strands, ambiguous role attachment,
missing obstacle slices, and profile jumps exceeding one transverse cell per
slice. Nearest feasible obstacle tie-breaking is an explicit totalization, not
an independently inferred universal ARC law. Unmodelled grammars are unverified.
The first Racket draft had a scope-parenthesis error; the corrected program
passed all supplied labels and subsequent protected generation checks.

Status: reviewer-ready after current preflight/audit. Source registration,
owner review, native qualification, acceptance and training admission remain
pending; no measured-learning claim is made.
