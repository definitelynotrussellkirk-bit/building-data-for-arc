# Independently aligned shape XOR and ordered subtraction

This reviewer-native family preserves production 3.0.0 and the exact canonical
XOR program. Its `combine=difference` setting subtracts the higher-color shape
from the lower-color shape after independently normalizing each to its top-left
origin. Only the canonical expression combining the two sets changes.

## Exact semantics and grammar

Input axes are 1..30. Inputs use exact built-in lists of equal-length lists and
exact integer colors 0..9. Exactly two nonzero colors occur, and each forms one
four-connected component. Shapes may have arbitrary size, holes and bounding
boxes; different-colored shapes may touch. Identical normalized shapes and strict
subsets are lawful. The grammar is broader than the sampler's shapes and the
production tetromino/size/palette restrictions; production itself is unchanged.

Sort the two objects by color, normalize them independently, then compute XOR
or ordered difference. Paint surviving cells cyan in the shared normalized
frame. Preserve blank leading rows/columns; use the maximum surviving coordinates
for output size, so canceled trailing extent disappears. An empty result is
exactly `[[0]]`. There is no final nonzero crop or rotation/reflection alignment.

Requests support exact integer seeds 0..2**63-1, 2..6 demos and 1..4 queries.
Defaults are three demos and four queries; qualification explicitly uses six.
Settings contain exactly `combine=xor|difference`. An omitted setting is drawn
once per episode. Separate SHA-256-derived RNG streams control the setting,
demo bank and query bank. The complete six-plus-four bank is built before
slicing; inputs match across settings, prefixes survive count changes, and each
call returns fresh lists.

## Teaching and size coverage

Core 0 uses two mostly shared square frames plus different internal/external
branches. Both settings produce blank leading row/column and cancel trailing
extent. Core 1 uses unequal L-shaped paths. Their size and bounding-area ordering
reverses core 0; their spatial/color order also reverses. Together they distinguish
recropping, union-frame rendering, direction, color/position/size role shortcuts,
and incorrect geometric alignment. Core orientations are fixed to preserve these
constructive witnesses; locations and non-cyan palettes vary.

| Slot | Canvas | Content |
|---|---|---|
| Demo 1 | 13x20 | Shared frame with unequal branches; lower color first and larger |
| Demo 2 | 14x23 | Unequal L paths; lower color last and smaller |
| Demo 3 | 1x2 | Touching singleton objects, empty result |
| Demo 4 | 7x12 | Independently posed tetrominoes |
| Demo 5 | 24x27 | Two connected 20x10 comb shapes |
| Demo 6 | 30x30 | Two connected 26x12 comb shapes; 360 foreground cells |
| Query 1 | 4x9 | Independently posed tetrominoes |
| Query 2 | 17x22 | Two connected 14x8 comb shapes |
| Query 3 | 26x29 | Two connected 22x11 comb shapes |
| Query 4 | 30x30 | Two connected 23x13 comb shapes; 346 foreground cells |

Comb shapes share a vertical spine and top/bottom rails. Interior rows vary
among A-only, B-only, both and neither in balanced shuffled blocks. This preserves
connectivity while making membership/cancellation depend on many cells spread
throughout the large canvas. The different 30x30 occupancies guarantee distinct
large demo/query inputs; other dimensions differ. Sampling is constructive with
no retries, label filtering or rejected draws.

## Real intermediate dependency

A extracts the color-ordered components and computes their independently
normalized coordinate sets. B consumes those sets to decide membership in the
ordered difference and render the surviving frame. Changing only A's second
stored set to its observed, unnormalized coordinates changes which cells cancel;
B's membership test and renderer remain identical. The causal witness retains
protected executions of these intermediate sets and of both full outputs.
This changes a geometric relation used by B, not merely paint color or code order.

## Evidence boundaries

The independent audit fits named rivals only to the first two demos, freezes
every survivor, then scores all four queries. It checks all generated labels
with independent Python and protected Racket. Commutative operand-order aliases
under XOR must be reported honestly. Finite seeds and rivals do not prove
universal identifiability. The shared sampler checks request contracts; preview
checks validate serialization and do not independently replay labels.

The two inherited review entries remain `needs_triage`: the old inert-extra-
objects finding names superseded source, while the current-source audit reports
no issue. This extension does not automatically close either entry. Reviewer
readiness remains separate from exact-source owner acceptance and training use.
