# f48cc30d7943 — current generator decisions

## Rule and domains

Version **3.0.0** keeps Racket authority **8c735fdd2a75** unchanged. Partition the
finite canvas into four-connected components of every color except 5. Count
individual color-2 cells. In components with exactly two, replace only original
zeros with 8; preserve every nonzero value, including preexisting 8. Neither a
rectangular chamber nor enclosure by gray walls is a rule precondition.

`rule_grid_errors` checks the ARC interchange envelope: a rectangular list of
lists, each dimension 1..30, exact integer digits 0..9. `self_check` adds a
teaching grammar: at least two non-5 components, a two-red component containing
a zero, and a differently counted component containing a zero. The sampler is
a narrower constructive distribution, not a claim to enumerate this grammar or
the full reference domain. `reference_model` is an authoring diagnostic; Racket
remains the dataset label source.

## Distribution and lesson contract

Default sample indices repeat a period of three. Residue zero draws framed
rectangular rooms at 10..12 on both axes. Two-thirds of its layout choices select
two room rows and two columns; the remaining branch selects a feasible 2..9-room
layout. Room sides are at least two; all compositions of the remaining dimensions
and all placements of 0..3 reds in each room have constructive support, subject
to a positive/negative contrast. This includes the shapes and seed arrangements
of all five canonical examples, without loading their arrays during generation.
The strict profile recognizes the framed four-room canonical geometry.

Residues one and two draw six diagnostic chambers, with random feasible active
dimensions, translation, D4 orientation, seed positions, and a foreign color
from {1,3,4,6,7,9}. Their counts are two, four, five, two, one, and three:

- A winding open positive has red cells at least nine Manhattan steps apart,
  a non-cyan articulation between them, preexisting cyan beyond them, and a
  zero whose graph distance from either red exceeds the maximum canvas dimension.
- A four-red negative contains the same foreign and cyan marker colors. Its
  diagonal contact with the positive distinguishes four- from eight-connectivity.
- A thick nonrectangular five-red negative prevents a thick shape from implying
  qualification. An enclosed thick L positive has an adjacent pair of red cells.
- A one-red negative touches that L diagonally. A separate open three-red
  negative prevents boundary contact from implying qualification.

The active stencil uses AH>=11 and AW>=10, AW<=canvas width minus two, and
2*AH+AW-6 greater than the maximum canvas dimension. Feasible pairs are selected
directly, without retries, clipping, or fallback labels. A full gray column
separates the final open negative. These constraints remain feasible at every
supported rich size, including 12x28 and rotated 28x12 intermediate canvases.

`EXAMPLES_NEEDED=3`. For default generation, any four consecutive draws contain
at least two diagnostic examples; any single-query holdout leaves one in the
three demonstrations. Every diagnostic example refutes all **27 declared rivals**
(24 canonical-fitting alternatives and three already refuted by canonical data).
The hook scores the supplied labels; it never silently relabels a demonstration.
This is a finite-bank teaching guarantee, not uniqueness among arbitrary rules.

## Public API and migration

Only exact `grid_h` (7..26) and `grid_w` (7..28) controls remain. Both work jointly
in every difficulty. Known `None` values mean omission; unknown keys, including
unknown `None`, are errors. Controls reject bool, float and string coercion.
Difficulty is None/easy/medium/hard; None selects medium. Small explicit sizes
use framed rooms and carry no diagnostic-witness or lesson-rotation promise.
Default rich bounds are easy 12..16 by 12..16, medium 12..20 by 12..22, and hard
12..26 by 12..28. Framed defaults remain 10..12 in every band.

Version 2 advertised room-count, palette, position-bias, seed-count and texture
options it ignored or treated inconsistently. Those controls and the explicit
no-walls/no-seeds/all-qualify degenerate modes are removed rather than silently
accepted. The earlier source emphasized rectangular room diversity; further
rationale was not recorded. The new choices preserve canonical support while
showing the semantic distinctions absent from that distribution.

An intermediate 3.0.0 source kept diagnostic red pairs adjacent or nearly so.
The independent review found a real seed 31/easy lesson at indices 0..3 that fit
a distance<=8 rival in all demonstrations and contradicted it in the query.
`counterexamples/seed_separation_before.json` retains the exact lesson. The
final layout deliberately widens one red pair and supplies negative shape and
boundary controls; the strengthened tests failed before this change and pass
after it. The first active-height 10 design merged chambers; it was rejected.

## Evidence and remaining decisions

`tests/` contains the independent oracle fixtures, 200 collected test cases,
1,760 joint size draws, 96 additional boundary/residue draws, and 432 holdouts.
`workspace/probe_semantics.py` dynamically discovers actual rival declarations,
calls the public Racket apply command, and retains exact labels/source bindings.
The returned review also retains the before battery, both real RED runs,
intermediate results, final checks, larger lesson censuses, and exact-patch replay.

The official after battery still reports a blocking `transformation_drift`
warning: its palette-set difference misses newly painted cyan pixels when cyan
already existed in the input. The inputs do contain visible zero-to-eight edits.
A generic, separately tested optional checker patch is included in the return;
it is not installed into this task delta. Maintainer review of that checker
finding is the remaining acceptance decision.

Known sampling limits include gray walls, at least two chambers, fixed semantic
colors, structured diagnostic geometry, and restricted room-count/seed-count
support. Single-component, wall-free, wider shapes, and unrestricted negative
counts are valid reference extensions but are not promised by default lessons.
The frozen imported catalog may still display version 2.0.0/its old summary until
maintainer refresh. Such imported metadata or an old approved hash does not
approve these new bytes; this return does not grant training admission.
## Current reviewer considerations

Source SHA-256: `b132d7379dbffedb658594771b419d949fd817319fc8b3687e5c1bc04585d595`.

# Distribution decisions — f48cc30d7943

The selected baseline is version 2.0.0, source
`31b6a227823454591901f3f019f3e47e1d71f020b2a6ccd03140a14cabda584d`.
The final version is 3.0.0, source
`b132d7379dbffedb658594771b419d949fd817319fc8b3687e5c1bc04585d595`.
No Racket source, canonical label, shared implementation or audit target changed.
The previous notes contained no design rationale beyond the generator's stated
aim of improving rectangular-room diversity; unrecorded rationale is unknown.

## Decisions and alternatives

| Choice | Earlier behavior / alternative | Decision, reason and evidence |
|---|---|---|
| G1: chamber semantics | Full gray wall lines and solid rectangular rooms only | Use actual four-connected non-5 components in authoring checks. Racket traverses foreign colors and existing 8, and accepts open/bent chambers. Tiny exact reference cases and the final semantic probe verify those distinctions. |
| G2: exact controls | Several advertised axes were ignored; size bounds were not honored | Keep only exact height 7..26 and width 7..28. Use strict keyed draws and observable dimensions, rejecting unknown keys and coercions. The focused suite executes all 1,760 joint size/band combinations and 96 additional size/residue draws. |
| G2: difficulty and None | Unsupported difficulty values silently selected a fallback | None means medium; only easy/medium/hard strings are accepted. Known size None means omission, including RNG behavior. Unknown None is still an error. |
| Canonical support | Unframed rooms with sides 2..5 could not construct the original framed arrays | One scheduled profile has a full frame, sides at least 2, variable 2..9 rooms and counts 0..3. A weighted four-room branch retains strict canonical support without copying canonical arrays. All 5 canonical pairs pass the strict hook; final strict rate 134/600. |
| Visible positive/negative contrast | Rectangles and maximum 3 reds were treated as semantic invariants | Teaching validation instead requires at least two components, one exactly-two-red component with a zero and one differently counted component with a zero. This is narrower than the reference, broader than the sampler. |
| Diagnostic counts | Counts 0..3 could not distinguish equality-to-two from positive parity, two modulo three, or two-or-high-count rules | The rich profile includes visible negatives with 1,3,4,5 reds and two positive chambers. Existing cyan and a foreign marker occur in both a positive and a negative component, avoiding marker-activation correlations. |
| Topology and reach | Rectangles allow full-line, bbox, shape and short-range shortcuts | Winding C, enclosed thick L, bbox decoys, diagonal contacts, colored articulation and a long graph tail distinguish these rules constructively. The tail inequality is enforced when choosing feasible dimensions. No retry or label-dependent resampling is used. |
| G3: nearby-pair repair | Intermediate positive red pairs were always adjacent or distance 2 | Independent Racket evidence found easy/seed 31/indices 0..3 with a nearby-pair rival fitting every demo and contradicting the query. Move one pair at least 9 Manhattan steps apart, retain the adjacent pair, and add the rival to all relevant contracts. Original and final exact lesson evidence are retained. |
| G3: shape controls | Intermediate positives correlated with open or thick nonrectangular geometry | Add a thick nonrectangular five-red negative and a separate open three-red negative. Add the precise shape selector and boundary-activation alternatives. These changes address observed template correlations without claiming unrestricted shapes. |
| Teaching schedule | Independent random witness frequency does not guarantee a useful lesson | Use framed/rich/rich, period 3, EXAMPLES_NEEDED=3. Four consecutive defaults contain at least two rich samples. Any single-query holdout leaves a rich demonstration. Final 300 production lessons/1,200 rotations and9 fixed-seed cyclic lessons/36 rotations found no ambiguity in the 27-rival bank. |
| Small exact sizes | A full diagnostic stencil is infeasible below 12 on either axis | Honor the requested dimensions with constructive framed rooms. Do not claim the default rich-witness or query-rotation contract for explicit small controls. A false profile label cannot make the small geometry diagnostic. |
| Rule authority | Expanding the rule to match a convenient sampler would alter the task | Keep Racket hash 8c735fdd2a75 unchanged. Use a separately validated Python mirror only for authoring, witnesses and tests. Retained production labels always come from the public Racket runtime. |
| T1: drift checker | Removing cyan, reducing its frequency or suppressing the warning would conceal a useful semantic case | Preserve the actual checker failure. The shared detector confuses global palette growth with new painted cells. Include a generic optional fix and 28 RED/GREEN-focused tests, without editing the selected shared source or claiming a patched full battery. |

## Constructive limits

Rich canvases are at least 12×12; the active stencil has AH>=11 and AW>=10.
Select feasible `(AH,AW)` directly so `2*AH+AW-6 > max(canvas_h,canvas_w)` and
`AW <= canvas_w-2`. A full gray column separates the open negative. Minimum
capacity retains original zeros in all six chambers. D4 orientation is applied
after choosing transposed working dimensions when necessary, so exact requested
height/width survive quarter turns. All random samples from sets use sorted
coordinates; the global random state is untouched.

The earlier active-height 10 hand design merged its L chamber with the one-red
negative. It is retained as an intentional boundary diagnostic, not an accidental
solver failure. Earlier no-cyan and positive-only-cyan designs left additional
marker alternatives; their actual checked outcomes are also retained.

The finite bank has 24 alternatives fitting all 5 canonical pairs and 3 secondary
alternatives already contradicted by canonical labels. The census records all
namespace-qualified entries, which duplicate some callable rules; this return
reports 27 distinct named rules, not 78 independent hypotheses. Witness predicates
are validated against actual supplied grids and Racket labels. The lesson hook
must use supplied demo/query labels, including deliberately alternative-labelled
inputs in a focused purity test.

Default data still uses fixed red/gray/cyan roles, gray walls, at least two
components, structured six-chamber diagnostics, and a bounded set of counts.
Wall-free/single-component variants, arbitrary negative counts and unrestricted
topologies remain outside the sampling claim. Sampling a valid subset of the
reference domain is intentional; a finite rival pass is not universal induction.
Task-local notes disclose stale imported catalog version/summary fields pending
normal maintainer refresh. Old approval metadata does not approve new bytes.

## Evidence and acceptance policy

All genuine failures remain: the initial baseline tests, intermediate strengthened
tests, both intermediate/final checker warnings, the discovered actual lesson
gap, and setup ENOSPC. The optional checker's RED failures are intentional tests
against a real checker defect; the stale-binding probe is explicitly intentional.
Neither is presented as an accidental solver error.

The two solve episodes are separate. The blind task was completed before repair
source exposure. The post-repair episode uses final generator bytes, visible
examples only during solving, and an honest earlier-exposure=yes declaration.
Query correctness is withheld and remains unknown. The work logs are authored
notes and program revisions, not token-level model traces.

Acceptance needs attention solely for the remaining strict checker result. The
packet limits source edits to the selected task, so the generic checker fix is a
reviewable separate proposal. Audits are findings-only and do not approve their
targets. No check in this return grants training admission.
