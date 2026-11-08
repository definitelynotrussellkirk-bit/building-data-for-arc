# Current decisions: 04c98e3e35bb

## Selected semantics and controls

`generator.py` selects version **3.2.0**, with unchanged canonical Racket rule
pin **`264a1a87abe5`**. The authority is
`shared/data/base/solutions/custom/705dfdee__04c98e3e35bb.json`.
The runtime's `(objects grid 0)` detects same-color four-components, not
color-blind components. Border components become 2, strictly interior components
become 8, and fixed background 0 stays unchanged. Input colors 2 and 8 are legal.

The former palette exclusion, small-profile exclusion, cell-based interior
check, and silent count clamping have been removed. Validation checks shape,
integer colors, fixed background presence, and both component classes; an
interior cell inside a border component is insufficient. It accepts canonical
inputs and component counts above the generator's requested-count limit.

Dimensions 6..25 and component counts 1..4 are exact observable overrides in all
difficulty bands. Zero counts are outside this production domain. `obj_color`
anchors the first foreground cell in row-major order after geometry and
orientation; it does not force every object to that color. `mixed_colors=False`
does force a monochrome foreground; true guarantees at least two colors.
`observe_overrides` reports these realized properties.

`texture` controls the shape mixture; `obj_shape` is its checked alias, and
conflicting aliases are refused. Size bounds govern random construction scale,
not observed cell counts or bounding-box extrema: T uses at least 3, and
L/line/plus at least 2. Singletons ignore scale in the mixed distribution, while
explicit `single` plus explicit scale controls is refused. Explicit shapes are
not silently shrunk. A bounded placement refusal may mean an infeasible request
or unsuccessful search; it names relevant axes and never returns fewer objects.
Any nonempty effective override selects free packing, with roomy defaults for
unspecified dimensions, and does not retain the default lesson guarantee.

## Teaching design and resolved failures

The default 16-index semantic schedule has three contact draws for every free
draw. Every band includes the canonical dimension profiles 6×6, 7×7, 8×8, and
7×9. Contact grids start with congruent same-color L components with opposite
border status, connect them through a different-color bridge, and supply
interior input colors 2 and 8. They conditionally extend the border L as described
below. Free layouts supply arbitrary component placement and
additional shapes/aspect ratios; their size ranges depend on difficulty.

The selected finite rival contract contains `global_color`, `color_blind_4`,
`same_color_8`, `color_blind_8`, `edge_cells_only`, `preserve_input_2`,
`force_input_8_red`, **`degree_two_loop`**, and **`largest_component`**. The latter
two heuristics were independently authored from earlier visible demonstrations.
`edge_cells_only`, `degree_two_loop`, and `largest_component` are refuted by
canonical examples, so none is declared a canonical shortcut. They remain useful
competitors for generated lessons.
The lesson hook requires each competitor to be refuted by an actual
demonstration, without consulting masked query labels.

Three prior choices were reversed after concrete failures:

- **v3.0.0 corner placement → v3.0.1 interior arm:** allowing offset 0 could put
  every cell of the border L on the boundary. The retained 300-lesson census
  found **2/300 ambiguous production lessons and 14/1200 ambiguous rotations**
  against `edge_cells_only`. Restricting the offset to `1..w-5` guarantees an
  interior arm cell whose red label teaches whole-component propagation.
- **v3.0.1 motif alone → v3.1.0 isolated border object:** the independently
  authored degree-two-chain heuristic exposed **21/300 ambiguous lessons and
  117/1200 ambiguous rotations** when rescored on separate saved authoring
  census data. Each contact grid now adds a border domino, or isolated singleton
  if necessary, in a clear eight-neighbor halo. Its symbol also occurs in the
  main motif, so the rival's singleton-color filter cannot remove it. Its
  structural degree is at most one: canonical output is red, rival output cyan.
- **v3.1.0 congruence alone → v3.2.0 conditional border extension:** a subsequent
  independently authored solver selected one largest same-color four-component
  per color for cyan, broke ties by earliest row-major component, and colored
  the other components red. Rescoring separate saved authoring census data found
  **2/300 ambiguous lessons and 20/1200 ambiguous rotations**, with no execution
  errors. Before adding the isolated degree witness, compare the two main L
  components' first coordinates. If the interior L is earlier, add one empty
  adjacent boundary cell to the border L, explicitly avoiding a merger with the
  interior L. Otherwise retain their equal sizes. The largest/first component
  is consequently a border component in either case, so the rival's cyan choice
  is wrong. The later domino/singleton has at most two cells and cannot change
  that winner. This does not change component counts, palette, diagonal contact,
  or the interior arm needed for propagation.

The extension and extra object preserve palette cardinality and all interior witnesses.
Contact grids now have two border components, or three in the palette-5 profile,
and three or four interior components. For current profiles, a clear position
always exists: the opposite border lies beyond the motif's clearance halo, and
the one or two interior singleton additions can block at most three border
positions each. Future profile changes must revisit this placement argument.
The conditional extension is adjacent to the existing border L and does not
consume clearance on the opposite border.

## Evidence, tooling, and remaining limits

`tests/test_border_semantics.py` uses an independent component oracle for
canonical acceptance, exact controls, malformed grids, contact distinctions,
and lesson witnesses. `counterexamples/component_contacts.input.json` and its
reference/evidence companions retain hand-authored color-blind-four and
same-color-eight witnesses labelled through the public Racket apply path.
`workspace/probe_components.py` reproduces those reference/rival disagreements.

`workspace/rescore_authored_rival.py` is a task-local prototype for saved,
labelled **authoring census** data. It reuses retained labels, verifies instance
hashes, requires exactly one query per lesson, and executes rival code from
captured source bytes whose hash is recorded. It does not score solve episodes
or read their private query labels. Its caller remains responsible for
rule/source provenance; it is not a replacement for the public census's full
validation or an approval gate.

The 75% motif curriculum intentionally concentrates geometry and forces
interior input colors 2 and 8. The free quarter broadens support but does not
make every lawful layout equally likely. Nine-rival lesson checks and query
rotations are finite evidence, not universal identifiability. The current source
is `4a98b688f9b3ae54ed1f0b956b946a1610831961c87a8cd53a118d69b393c555`.
The final v3.2.0 battery passed all 12 stages; portable tests passed 113/113.
The 300-lesson census contains 1,200 pair occurrences and 1,199 unique inputs,
with zero production or rotation ambiguity, warnings or errors against nine
rivals. Fixed-seed enumeration covers 48 lessons/192 rotations/27 unique inputs
with the same zero findings. Both independently authored shortcut programs
also have zero measured ambiguity on final saved authoring labels. These
results do not confer training approval. Imported associated notes remain in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4a98b688f9b3ae54ed1f0b956b946a1610831961c87a8cd53a118d69b393c555`.

# Decisions for 04c98e3e35bb

Assignment: `review-c033d0d79cd6eda2`. Final generator: v3.2.0, SHA-256
`4a98b688f9b3ae54ed1f0b956b946a1610831961c87a8cd53a118d69b393c555`.
Evidence paths are relative to WORK, the returned packet root. Compressed
evidence restores to the original paths described in REVIEW.md.

## D1 / R1: Follow the existing component rule

The runtime's `(objects grid 0)` means same-color four-connected components.
The canonical rule recolors a whole component red (2) if any cell touches the
canvas edge, and cyan (8) otherwise. Background is fixed at 0. The old summary
omitted the color distinction; a one-color, separated-object distribution made
color-blind components, eight-connectivity, and per-color grouping plausible.
The original design rationale is unknown; no substantive current rationale was
recorded in notes.md. Historical imported material was used only as context,
not as evidence that this exact baseline was repaired.

Keep the canonical Racket program and all canonical examples byte-for-byte.
Synchronize only the selected archive's `racket_target.target_code` to that
canonical text; its discrepancy was a comment, not different execution. Keep
the archival `raw_code`. Pin `RULE_HASH = "264a1a87abe5"`. Changing the Racket
rule to color-blind connectivity was rejected: it would redefine the task to
fit a narrow generator. The two authored contact witnesses in
`repo/generators/04c98e3e35bb/counterexamples/` are labelled by the public Racket
API and separate the competing component interpretations.

## D2 / R2: Restore lawful palettes and small profiles

The baseline validator rejected two of four canonical inputs because they
contain input 2 or 8. Its 60-draw profile check had zero matches in every band.
The repair permits every foreground color 1..9 and validates actual components,
not merely the presence of an interior cell inside an edge component.

The default semantic schedule includes all four canonical canvas/palette
profiles in every band. Their dimensions are 6×6, 7×7, 8×8, and 7×9; background
inclusive palette sizes are respectively 4, 5, 5, and 6. Contact examples force
interior occurrences of input 2 and input 8 so fixed output colors cannot be
mistaken for immutable input colors. Injective color mapping preserves symbolic
component identity. When specified, `obj_color` binds the first occupied cell
in row-major order after geometry/orientation; `mixed_colors=False` separately
requests one foreground color.

An all-small curriculum would overrestrict support. Retain a free-layout draw
at every fourth index, with wider band-dependent sizes and shapes. A wholly
random layout was also rejected because rare discriminator events could leave
short lessons ambiguous. The chosen 75% contact / 25% free mixture is an explicit
teaching bias, not an estimate of the natural frequency of these shapes.

## D3 / R3: Make exact controls observable

Explicit dimensions span 6..25 in every band. Exact border/interior component
counts each span 1..4 and are checked after placement. Zero counts were removed
from the advertised production domain: both classes are required, and the old
advertised zero values already failed. Unknown keys, invalid types, conflicting
shape aliases, and invalid values fail explicitly. Difficulty affects defaults,
not the legality of an explicit dimension or count.

`texture` owns shape choice, with `obj_shape` as a compatibility alias rather
than a duplicate axis. Size controls remain construction scales (minimum 1..5,
maximum 2..6), not exact cell counts or bounding-box extrema. T has intrinsic
minimum scale 3; L, line and plus have minimum 2. Explicit singleton-plus-size
combinations and minimum-above-maximum are incompatible. Treating every scale
as an exact pixel count was rejected because it would change the established
shape API. These limits are now documented rather than hidden by a fallback.

Packing enumerates valid origins and preserves requested component identity,
allowing different colors to touch while preventing a same-color orthogonal
merge. It has bounded retries; a refusal can mean unsuccessful search as well
as infeasibility. It must name the relevant axes and must not silently reduce
the requested object count. Default mixed packing may use a singleton on a
final retry; an explicit shape is never silently replaced. Any nonempty
effective override selects free packing and loses the default lesson guarantee.

## D4 / R4: Test complete lessons and preserve failed designs

The declared semantic period is 16. Three consecutive contact positions and
one free position repeat; contact profiles rotate across this period. Training
lessons request three ordered demonstrations and one query. The production
sampler may advance accepted indices. Required query rotation holds each of
the four materialized pairs out once, preserving the remaining order.

Version 3.0.0 already passed all twelve standard stages, but the 100-per-band
census found 2/300 ambiguous production lessons and 14/1200 ambiguous rotations
against `edge_cells_only`. An L placed at a corner could have no interior arm
cell, so its red output taught no propagation. Version 3.0.1 moved the motif
offset to 1..w-5. The full failing lesson and failing focused regression are
retained; this was a real failure, not an invented negative.

Version 3.0.1 passed the enlarged census against its seven declared rivals.
An isolated visible-only solver then authored a different heuristic based on
degree-two structures, filtering globally singleton colors. Rescoring that
actual program against the separate labelled authoring census found 21/300
ambiguous lessons and 117/1200 ambiguous rotations. This did not inspect or
score either private solve query. The frozen earlier solve, exact rival program,
full source-bound rescore and minimal failing lesson are retained.

Version 3.1.0 adds an isolated same-symbol border domino, with singleton fallback,
to each contact draw. The rival predicts cyan on its degree-zero/one cells;
the canonical rule predicts red. Its repeated symbol prevents the rival's
singleton-color filter from discarding it. The existing contact and palette
witnesses survive. Source review established that current profiles always have
a clear position; changing their dimensions/singleton count must revisit that
argument.

### R6: Refute a second independently authored shortcut

The v3.1.0 isolated solver authored a different rule: find same-color four-connected components, select one largest component per color for 8, break equal-size ties by the earliest row-major cell, and paint the remaining components 2. Its first actual revision matched 3/3 visible demonstrations. Separate saved authoring labels exposed 2/300 ambiguous production lessons and 20/1200 ambiguous rotations, with zero execution errors and 1,198 unique inputs. This is a second concrete miss by the declared-rival bank, rather than an extrapolation from the earlier degree-two failure. `checks/final-solver-authoring-rescore.json`, `checks/prior-solve-v3.1.0/`, `workspace/largest_component_rival.py`, and `counterexamples/authored_largest_component_lesson.json` retain the result and exact program. No private query correctness was used.

Version 3.2.0 applies a conditional size discriminator after orientation: if the interior L precedes the border L in row-major order, grow the main border L by one adjacent empty edge cell. If the border L already wins the tie, retain its size. The authored rival therefore chooses a border object for cyan in every contact profile, disagreeing with the true border rule. Preserve the separate isolated border object because it independently refutes degree-two behavior. Rejecting the ranked heuristic only in a scoring hook was inadequate; the materialized demonstration must contain the discriminator. The focused new regression genuinely failed on v3.1.0 (1 failed, 112 deselected), and the post-repair suite passed 113 tests.

The current nine competitors are global-color grouping, color-blind four- and
eight-connectivity, same-color eight-connectivity, edge-cells-only recoloring,
preserving input 2, forcing input 8 red, the authored degree-two heuristic, and the authored largest-component-per-color heuristic.
The six declared canonical shortcuts fit all four usable canonical pairs;
edge-only, degree-two and largest-component are lesson competitors, not claimed canonical fits.
The final census checks actual declarations, with seeds derived from
`sha256('lesson-census:v1:TASK:BAND:INDEX')[:8]` as uint32, indices 0..99 in each
band. The separate schedule run enumerates starts 0..15 at seed 0 in all bands.
The current return census has 300 lessons, 1,200 pair occurrences, 1,199 unique inputs and 1,200 query rotations, with all ambiguity/warnings/errors zero. The fixed-seed schedule has 48 overlapping windows, 192 rotations and 27 unique inputs, again with all ambiguity/warnings/errors zero; it is not 192 independent random draws.

## D5 / F1: Build a reusable authored-rival rescorer

`workspace/rescore_authored_rival.py` accepts a saved labelled authoring census
and a local Python `solve(grid)` program. It verifies instance hashes, captures
the rival source bytes and hash before execution, validates returned grids,
caches predictions by input hash, and reports production and every single-pair
holdout separately. It requires exactly one query per lesson. Exit 0 means no
measured ambiguity, 1 means ambiguity, and 2 means invalid evidence or execution
errors. It never treats an execution error as a clean semantic result.

This task-local prototype is ready for reuse on trusted local programs; it is
not a sandbox or the public census's complete evidence validator. A shared
version should compose with the existing public rescore validation and bounded
execution machinery. No shared runtime/controller was changed.

## D6: Honest scope and remaining choices

The v3.1.0 eight-rival census and fixed-seed enumeration passed, then a new independently authored rival exposed ambiguity. Final v3.2.0 nine-rival production and rotation counts are 0/300 and 0/1200 ambiguity (1,199 unique inputs); fixed-seed enumeration counts are 0/48 and 0/192 (27 unique inputs), with all errors/warnings zero. Independent external-program final rescores in `checks/authored-degree-return.json` and `checks/authored-largest-return.json` each report 300 lessons, 1,200 rotations and 1,199 unique inputs, with zero production ambiguity, rotation ambiguity and execution errors (exit 0). The final battery passed all 12 stages; the new isolated solve passed all 3 visible examples in one revision. Exact-patch replay passed: all 113 focused tests ran again in the fresh isolated runtime, compressed evidence restored, and both a historical failing and final passing rescore reproduced. A finite rival list cannot establish unique induction among all programs. The rich
curriculum still exposes a repeated geometry and a distinctive interior-2/8
palette; the free quarter reduces concentration without making every lawful
layout equally likely. Broader adversarial programs may reveal another gap.
Acceptance is a source repair decision, not automatic training admission.

Both audit findings are separate and unpatched: A1 concerns midpoint-only
notches; A2.1 concerns monochrome support hiding same-color segmentation. Their
public Racket witnesses and source hashes are in AUDIT.md. Unrelated sources,
frozen fixtures, shared checks, assignment draws, and canonical rows were
preserved. The original archive remains the replay authority.
