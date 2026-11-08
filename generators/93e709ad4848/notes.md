# Review notes — 93e709ad4848

## Correct authority and original defect

The canonical task is **Nearest-Corner Dock**. The imported generator described
and generated recoloring several objects by Manhattan-distance neighbor degree.
The canonical rule, its task-local selected authority, and the canonical examples
agree on docking one object. None of those authorities was changed.

Reference pin: `684dd7c8349b`. Final generator SHA-256:
`c088bea0c98c51f4c651785b5dea8fe0f086fccb97c7802ecd07b7cf52e58e07`.
Original generator SHA-256:
`efbb6f66bb718eb6b3ef52e07ca00fd12a253cdc3e54ed442934b1a476c99bdf`.

The return's baseline probe used seeds 0..9, sample index 0, in all three bands.
All 30 inputs contained multiple components, passed the original validator, and
lost foreground pixels under actual canonical Racket execution. Four out of four
canonical inputs were rejected by the old validator. See the source-bound return
for the original receipts; old behavior is not an alternate authority.

## Input distribution

The cycle is `(seed + sample_index) % 3`: boundary, tie, rectangular. Defaults
contain one nonzero-color 4-connected shape and always move. They use five finite
shape families: ell, zigzag, hook, ring and rectangle, with profile-conditioned
orientations. These are input constructors, not output authorities.

Boundary examples place a top-heavy hook just beyond the bounding-box midpoint.
This separates bbox center from source anchor, first pixel, occupied centroid and
half-cell shifted midpoint. Placement also disagrees with the canonical color
lookup while colors remain marginally uniform.

Tie examples center an ell or hook missing its top-left bbox cell. They establish
fixed top/left priority and separate bbox center from nearest foreground pixel.
The positive translation-space check prevents a full-height or full-width object
from falsely claiming a distinguishable tie branch.

Rectangular examples place both center coordinates between the height and width
midpoints. They expose using one dimension for both axes. The rectangular shape
family is fixed by seed, while dimensions, orientation and placement vary. This
ensures a ring query is preceded by a ring demonstration in a three-demo stream.
The public sampler can reject duplicate pairs and continue. Two of the 300
measured default episodes did so; the accepted lessons still meet the finite
rival contract. No artificial color cycle was added to eliminate lawful retries.

## Overrides and domain boundary

Exact controls: `grid_h`, `grid_w` in 6..24; `object_color` in 1..9;
`shape_kind` in ell/zigzag/hook/ring/rectangle. All 16,245 finite combinations are
constructive. Unknown keys, wrong types, booleans for integer axes, out-of-range
values, and explicitly supplied `None` are rejected. Omit an axis to use its
default. `difficulty=None` remains valid.

`observe_overrides` reconstructs the controls from pixels. Explicit overrides
may remove a scheduled witness; they retain the lawful one-object domain and a
visible move. The default lesson guarantee does not apply to arbitrary overrides.

`self_check` and `strict_canonical_like` accept a rectangular 1..30 grid with zero
background and one nonempty monochromatic 4-connected object. They accept lawful
one-dimensional and already docked shapes. These are absent from the normal
curriculum. A legal input is not necessarily an informative demonstration.

## Verification and limits

Seventeen focused regression methods include every finite axis tuple, all four
canonical pairs, literal tie/centroid/rectangle/hole cases, structural witness
claims and 900 cyclic hole-preservation lessons. The source-bound lesson probe
checks 100 seeds per band, both queries, all three starts, actual sampler retries,
and all declared canonical shortcuts/lesson competitors. It measures 783 unique
inputs across 2,100 band/seed/index tuples; cross-band overlap is explicit.
Public Racket parity is a separate required step; diagnostic Python labels never
replace reference-derived export labels.

The curriculum is deliberately compact. Profiles correlate with target corners,
and five shape families do not cover all connected shapes. Difficulty is not a
measured strict ordering. Passing finite-rival tests does not establish universal
induction or a measured model-training improvement.

The final battery retains one warning: `selfcheck-minimal-impostor` accepts
singleton, short_line and solid_2x2 shapes. These are lawful under the one-object
docking authority; 18 actual Racket checks preserve their shapes/colors/canvases.
The task-local repair cannot change that shared linter. Do not mark this candidate
approved or the complete battery green until the maintainer resolves the warning
and reruns the required checks.
## Current reviewer considerations

Source SHA-256: `c088bea0c98c51f4c651785b5dea8fe0f086fccb97c7802ecd07b7cf52e58e07`.

# Decisions — review-6635751a81a3f0a3

## F1 — restore the correct task domain

The original generator's rationale for using a different task is unknown. Its
comments consistently describe touch-degree recoloring; the canonical examples,
written solution and synchronized selected authority describe Nearest-Corner Dock.
Preserve the authority and replace the sampler. Changing the reference to fit the
old generator would contradict all four canonical pairs. The retained 30-pair
before probe demonstrates the consequence: multiple objects enter, only one exits.

## Input construction

Use one monochromatic 4-connected component on zero. Reject ragged or invalid-color
grids, disconnected same-color objects, diagonal-only contact and multiple colors.
Five small mask families are enough to cover asymmetric shapes, orientation,
solid rectangles and enclosed holes while keeping construction bounded and exact.
The broad semantic validator is independent of membership in this finite bank.
Arbitrary noisy multiobject inputs are outside this task's intended domain.

Keep substantial 9x9/9x11 and 8x8/10x10 scale support. Accept every advertised
6..24 dimension combination; observe all controls from pixels. Preserve colors,
shapes and holes, and let Racket generate exported labels. The Python oracle is
only a diagnostic and is separately checked against actual reference outputs.

## F2 — complete lessons must expose relevant alternatives

Random placement alone frequently leaves the bbox-center rule indistinguishable
from occupied centroid, source anchor, first pixel, nearest pixel, wrong midpoint,
wrong tie priority, wrong dimension and canonical color lookup. Declare executable
rivals and construct boundary, exact-tie and rectangular profiles. Any consecutive
three default draws include one of each, independently of the episode's start.

The first richer probe found an additional hole-preservation gap. An independent
"dock then fill enclosed holes" rule fits every canonical pair. Before the fix,
78/900 cyclic three-demo/two-query lessons admitted that rule on the demonstrations
and contradicted it on a query (seeds 0..99, three starts, all bands). These failures
were retained. Fix the rectangular shape family within each seed's stream, while
continuing to vary placement, orientation, color and canvas. Every ring query then
has a ring demonstration. Register that rival and its reference-checked witness.
The final regression scan has zero such ambiguous lessons.

A query-relevant rival may survive when it gives the same answer on both queries;
that is not an ambiguity. The final source declares 11 canonical-compatible
shortcuts and 13 total competitors. This finite set is an explicit scope limit,
not a proof that no other inductive shortcut exists.

## Exact controls, validation and witness corrections

Remove the old unimplemented axes instead of preserving fake control names.
All 16,245 tuples of the four advertised finite axes were exercised, plus per-band
boundary cases. Explicit `None` is an invalid supplied control; omitting the key
selects defaults. Preserve `difficulty=None` as the documented default band.

The independent review found full-axis objects that made structural witness
predicates fire even though both rival placements were identical. Require positive
translation space in the claimed axis. Keep the failing fixtures and positive
witness cases in the regression suite.

## Public sampler policy

The public worker rejects duplicate pairs and continues until it has enough
accepted pairs or exhausts its attempt budget. The final generator produces one
such retry in medium seed 28 and one in hard seed 28: rejected index 4 duplicates
index 1; accepted indices are [0,1,2,3,5]. Actual public generation reproduces this.
The initial task-local probe incorrectly promoted permitted retries to failure.
Retain that failed report and correct the probe to emulate public policy, with
an explicit optional `--require-no-rejections` diagnostic. Do not add arbitrary
color or geometry correlations merely to avoid two harmless retries. Domain,
reference, underproduction and lesson-semantic failures remain blocking.

## F3 — retain lawful tiny shapes and the honest admission blocker

The shared defect linter labels accepted singletons, short lines and solid 2x2
blocks as impostors, despite this task's unique-object translation semantics.
Eighteen actual Racket cases preserve their pixels, colors and canvases. Some are
identity cases, so they are not ordinary demonstrations; they are still lawful
inputs. Narrowing the validator to reject them merely to silence the generic
heuristic would encode an unsupported domain restriction. The task assignment
permits selected-task edits, not a shared-linter repair. Leave this failure visible
and the overall after battery failed pending maintainer resolution. No approval,
training-safety label, canonical rule, or audit-target generator was changed.

## Scope and stopping rule

F4, F5 and F6 are findings-only because the drawn audit tasks are outside the
selected generator's patch scope. F4's own lesson hook already detects its bad
cyclic window; the report does not infer an admission bypass. F5's rectangle
rival fails all canonical pairs but is ambiguous within some generated lessons,
so its result is not labeled a canonical-compatible shortcut. F6 is a deliberately
constructed unreachable-marker input; it is not counted among generated-domain
failures. The separate scopes and suggested fixes are recorded in AUDIT.md.

The baseline defect is repaired, focused tests pass, full lessons are measured,
and actual Racket parity is retained separately. The required blind and exposed
solve records each contain one genuine revision; masked correctness is withheld.
The two independently assigned audits are findings-only. Stop after their concrete
counterexamples and the source-bound return are complete. Remaining work is the
shared-linter disposition and ordinary maintainer admission, not further random
sampling or speculative model-training changes.
