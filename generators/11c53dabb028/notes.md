# Review notes: 11c53dabb028

Assignment `review-a71e4f549e8cb2c0` reviewed the pinned imported version 1.1.1,
not an unintegrated repair. The selected task has no retained review index and
its associated-notes file is empty; no task-specific prior return was used as
measurement evidence. Original author motives beyond code/axis declarations
are unknown.

## Defects and decisions

**G1 — domain validation.** The old validator could raise on malformed rows and
admitted non-ARC cell types and oversized inputs. The replacement checks shape,
strict integers, palette, bounds and the nontrivial zero/nonzero mask. It keeps
short lines, singleton foregrounds, and small solid components when embedded
in a lawful zero/nonzero grid. The rule acts on cells rather than requiring an
object grammar. The return includes 13 direct Racket checks for the shapes that
trigger the shared mutation heuristics. Rejecting them merely to silence those
heuristics would discard supported input cases.

**G2 — explicit controls.** Dimensions used to be constrained by difficulty;
density and color roles were not reliably observable; unknown and dead keys
could be swallowed. Version 2 defines final density by integer occupancy,
preserves pinned dimensions and first-color identity, and rejects removed or
malformed controls. The quantization/clamping is explicit so values at the two
endpoints still produce a nontrivial mask. A partial multicolor request must
choose a feasible free canvas if one exists. Structured incompatibilities are
reserved for genuinely impossible combinations and name only relevant axes.

**G3 — teaching support.** The four canonical pairs are square and monochrome,
so they do not resolve different nonzero-color selectors or rectangular period
choices. The generated distribution now supplies actual counterexamples.
The first attempted construction accidentally reserved a candidate column-major
cell rather than the actual earliest occupied cell; a retained test and six-pair
Racket-confirmed ambiguity caught this. Reserving the actual cell repaired it.
A subsequent independent review found that always making the first color
nonmodal allowed a second-frequency shortcut. Minimum/maximum profiles now give
the first color a strict majority, while middle profiles keep it a minority.
Both roles are redundant across the six-example window. The final probe checks
all declarations dynamically and every query rotation of actual production
lessons. The deterministic schedule can still encode correlations outside the
finite declared rival set; there is no universal induction claim.

**G4 — authority identity.** Pin `RULE_HASH = "573d7b5ea64c"` and synchronize the
selected base solution's `racket_target.target_code` to the unchanged canonical
source. Do not change the canonical ledger or archival `raw_code`. This removes
active authority text divergence while preserving history.

## Final measured evidence

All following final measurements bind generator SHA-256
`32cf2d21a7096a0f76115322813333a55e1ac27b1bba22567719db7ebfe02ac8`.
Paths below refer to the extracted return's `checks/` after optional evidence
restoration, not files expected inside this source directory.

- Battery: 11/12 green, zero pending; only `defect_lint` fails with zero errors
  and two mutation warnings. `checks/after-reviewed/` retains all stages.
- Exact override contract: 98,730 draws, 98,460 accepted, 270 declared/structured
  rejections, zero findings or warnings. Canonical profile floor: easy 8/20,
  medium 2/20, hard 7/20.
- Final production census: 300 complete five-demo/one-query lessons, 1,800 pair
  slots and 1,600 globally unique input grids. Every difficulty has 100 lessons.
- Task probe: all ten unique declared rivals refuted in every one of 1,800
  cyclic query rotations; 4,472 additional real-Racket comparisons with zero
  mismatches. It reuses the 1,800 authoritative census pairs.
- Joint override product: 5,400 fully specified requests; 4,464 accepted and
  936 expected infeasible. This does not exhaust partial requests. Separate
  partial-request regressions cover the concrete failure and metadata.
- Portable selected tests: 159/159 passed, including the Racket integration
  test, after making pytest available outside the disabled user site. The
  initial environment-only failed attempt remains retained.

`strict_canonical_like` names the declared lawful expanded task predicate.
Its 600/600 battery and 540/540 independent-default counts do not mean all those
inputs have canonical square/monochrome profiles. Exact profile hits are reported
separately. All training-admission flags remain unchanged.

## Evidence chronology and tools

The root return's `RESULTS.json` has exact commands, working directories, source
hashes and exit codes. `checks/regression-before/`, `checks/partial-overrides-before/`,
`checks/frequency-shortcut-before/`, and `checks/column-major-before.json` preserve
failures. Intermediate sources are retained under `checks/`; the workspace's
`semantic_review_intermediate*` files are explicitly intermediate.
`workspace/review_probe.py` implements the extended public-API semantic check;
`workspace/check_lawful_mutations.py` executes the 13 lawfulness fixtures.
The three task-local test modules exercise contracts, lesson rotation, reference
parity, partial feasibility and frequency shortcuts. Frozen imported fixtures
and shared tooling are unchanged.
## Current reviewer considerations

Source SHA-256: `32cf2d21a7096a0f76115322813333a55e1ac27b1bba22567719db7ebfe02ac8`.

# Decisions — 11c53dabb028

All decisions below apply to the selected task only. The pinned source was
version 1.1.1, SHA-256
`c55085227ebb6f0047bc7346cc85782659de57aa435f6533d5756d8cfcf89106`.
Its selected notes were empty, and there was no task-specific prior return index;
no prior return was used as a source of measured counts. Original design motives
are unknown unless inferable from explicit code/declarations. The final source
is version 2.0.0, hash `32cf2d21a7096a0f76115322813333a55e1ac27b1bba22567719db7ebfe02ac8`.

## G1 — input domain and validation

The meaningful domain is a rectangular ARC grid, dimensions 1..15, area at least
two, containing both zero and nonzero. Output doubling then remains within 30×30,
and excluding all-zero/all-filled masks avoids trivial outputs. These are
chosen generation constraints; they are not claims that Racket is undefined on
every excluded input. Check strict integer types so booleans, floating values
and out-of-palette cells do not slip through Python equality. Malformed nested
containers return a validator failure rather than raising.

An alternative was to reject singleton foregrounds, lines, small blocks, or
transpositions to improve the generic mutation score. That would impose an
object grammar on a rule whose transformation is defined cell by cell. The
13 explicit reference-backed fixtures show why that alternative was rejected.
All-background and all-filled examples remain invalid for this chosen
nontrivial domain, with dedicated must-reject fixtures. Evidence:
`checks/regression-before/`, `checks/lawful-mutations-reviewed/`, and
`workspace/mutation_heuristic_notes.md` in the patched task.

## G2 — exact controls and lawful feasibility

| Choice | Existing rationale / problem | Final meaning and rejected alternative | Probe / remaining limit |
| --- | --- | --- | --- |
| `grid_h`, `grid_w` | Advertised range conflicted with band-specific draw ranges. | Exact integers in 1..15 in every band. Difficulty changes unpinned weighting. Do not silently clamp a pinned dimension. | Full h×w joint product and task regressions. 1×1 is explicitly incompatible with the nontrivial mask. |
| Partial dimension requests | Drawing a free side first could make an otherwise feasible multicolor request fail. | Filter feasible dimension pairs from the complete request before drawing a free side; retain weighting among feasible choices. Do not retry arbitrary random draws or reject all partial combinations. | Original failures include `seed=8,index=0,grid_h=1,multi_color=True`; all 31 final partial/frequency tests pass. |
| `fg_color` | A present color need not be the color selected by the rule. | Exact first row-major nonzero identity, also under multicolor. | Test colors 1..9; final multicolor defaults observe all nine first colors in each band. |
| `fg_density` | Shared texture density did not reliably set final occupied cells. | Final count is `min(area-1,max(1,round(area*d)))` for finite numeric d in [0,1]. Python ties-to-even rounding is explicit. | Fully specified values 0,.5,1 plus targeted intermediate densities. This is integer occupancy, not an unquantized fraction guarantee. |
| `multi_color` | Type coercion and occupancy could make the request misleading. | Strict bool; true means at least two nonzero colors. False means one. | Multicolor needs two occupied cells and a zero; genuinely impossible requests carry only relevant `incompatible_axes`. |
| `texture` | Common texture helpers were being treated as if all modes were lawful. | Nine helpful modes are structural preferences before final occupancy, not guaranteed geometric outputs. | Reject all-zero/all-filled/monochrome mode names. Geometry is deliberately allowed to change under an exact occupancy request. |
| Removed `bg_density`, `noise_overlay` | Dead/conflicting controls could be accepted without observable effect. | Remove them from advertised axes and reject them, along with all unknown keys. | Initial regressions and public override contract. Version increases to 2.0.0 because accepted controls change. |

The final public contract exercised 1,097 cases in all three bands with 30 seeds:
98,730 calls, 98,460 accepted, 270 explicit rejections, zero findings/warnings.
The task probe additionally covers a fully specified 5,400-request product over
all dimension pairs, three density endpoints/midpoint, both multicolor states,
and None/easy/medium/hard. Its 936 rejections are expected infeasible tuples,
not observed valid-request failures. Neither measurement is an exhaustive proof
for arbitrary partially specified requests or all floating values.

## G3 — teaching distribution and schedule

Canonical inputs are 2×2, 3×3 or 4×4 with one foreground color. Keeping only
that population would preserve ambiguity between first, last, minimum, maximum,
mode, median and second-frequency color selection, and between height-only and
independent width/height periods. Expanding to arbitrary multicolor noise would
supply some counterexamples but would not ensure a complete lesson contains
one after holding out a query.

Use five demonstrations and one query with this period-six schedule:

| Residue | Profile | Teaching role |
| --- | --- | --- |
| 0 | Monochrome 2×2 | Canonical scale and palette support in every band. |
| 1 | Wide rectangle; middle-rank first color; minority | Refute extremes/mode, wrong scan order and square-only period. |
| 2 | Minimum-rank first color; unique majority | Refute median/maximum/second-frequency and wrong scan order. |
| 3 | Monochrome 3×3 or 4×4 | Additional canonical size support. |
| 4 | Tall rectangle; middle-rank first color; minority | Redundant middle witness when another pair is queried. |
| 5 | Maximum-rank first color; unique majority | Complement the minimum role and retain majority evidence under query rotation. |

Geometry, position, foreground identities, occupancy and mask preferences vary
within profiles. Each band retains a broad size tail; only probabilities change.
The two core positions protect canonical support, while disjoint observable
profile types reduce duplicate-induced lesson skipping. The shared sampler's
actual materialized instances, rather than a presumed raw sequence, are scored.
Every requested start residue appears in the 100-per-band sample; each accepted
six-pair lesson is rotated through all query roles. The first color is protected
against the actual column-major first and actual last occupied cells.

Rejected alternatives include always making the first color a minority, which
introduced a second-frequency shortcut, and reserving a merely proposed
column-major cell, which failed when another occupied cell preceded it. Genuine
failing tests and the retained six-input Racket witness document both repairs.
The period and profiles themselves may permit other correlations; ten named
rivals are a finite adversary set. No universal induction claim is made.
Explicit overrides opt into the general lawful domain, not this curriculum.

## G4 — reference authority

Keep the canonical ledger byte-for-byte unchanged (SHA-256
`08f88dbbda5279692992bc90a689c7b5cc6d426832557708666ecf8532146e41`).
The selected base solution's target text is synchronized with the canonical
program, and the generator pins normalized rule hash `573d7b5ea64c`. The raw
historical program text remains archival evidence. An alternative was to change
the rule to an easier color selector so the generator's old correlations were
less problematic; that would redefine the task and was rejected. Final authority
smoke, canonical outputs, and active text synchronization all pass.

## G5 — tooling and remaining policy decision

The reusable probe dynamically reads the actual rival dictionaries and their
namespaces, verifies source/census identity, and reuses authoritative production
pairs for the cyclic checks. Its Python mirror is diagnostic only; labels and
parity use Racket through supported public operations. The lawfulness checker
keeps small reviewed fixtures and expected outputs. Three new test modules are
inside the selected task and run through the portable task-test snapshot; no
frozen fixture, sibling generator or shared linter is patched.

Strict `defect_lint` still fails on two generic mutation warnings. Retaining the
lawful domain and escalating a concrete evidence-backed calibration choice is
preferable to a misleading all-green report. The detailed recommendation is F2
in `FEEDBACK_TO_CODEX.md`. Passing local checks does not grant training approval.

## Reporting and preservation

Keep the initial and intermediate failures, mark source hashes and distinguish
pair slots from globally unique inputs. Both visible-only solves retain their
single genuine revision and exact exposure declarations; no negative attempt
was fabricated. Compress large raw JSON losslessly with original path, byte
count and SHA mapping; test restoration before delivery. Apply the exact final
patch and rerun all selected tests in a fresh original extraction. Fresh replay
passed all 159 selected tests with identical generator/solve hashes; results are
in the final `RESULTS.json` and `checks/fresh-replay/`.

## G6 — proposed episode-fixed repeat-count prototype (2026-10-23)

Assignment `review-d02b5702e3d0eeff` leaves the approved production generator
and canonical rule unchanged. It adds an explicitly proposed task-local prototype
under `workspace/parametric/` with two independent rule parameters selected once
per complete episode: `vertical_repeats` and `horizontal_repeats`, each restricted
to exact integers in `{1,2}`. The canonical/default setting is `(2,2)` and its
Racket source is byte-identical to the current canonical program. The other three
settings change only the output height/width multipliers, preserving row-major
first-color selection, mask inversion, and periodic composition.

Each retained episode contains three demonstrations and four distinct queries.
The exact-Racket verifier covers all four settings, 28 intended pairs, 84
pair-level rival checks, 48 demonstration-only query-rival checks, all four
canonical pairs, and 12 `1x15`/`15x1`/`15x15` boundary cases. All intended labels
matched Racket; every other repeat setting was refuted by the demonstrations and
changed every query answer. Public files contain only demonstrations and
answer-free query inputs; their opaque IDs hash the exact visible bytes. Private
settings, seeds, programs, metadata, and query answers do not affect those bytes.

A separate adversarial pass covered 16 additional episodes, 32 pairs, 24 invalid
parameter attempts, output bounds, Racket/Python parity, rival separation, and
public/private projection stability with no observed failure. The full selected
task suite passed 167 tests. Evidence is retained in
`checks/parametric/11c53dabb028-repeat-count-v1/`. This remains a bounded
prototype, not production approval or training admission; its declared rivals
are only the other three repeat-count settings. The next useful promotion check
is an independent review against broader non-repeat-count rivals before any
production API or dataset identity is changed.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/11c53dabb028/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Native component-frame promotion

The current native adapter preserves all four retained repeat-count programs and
adds `input_frame=input|largest_component`, for eight settings. The default
`input, vertical_repeats=2, horizontal_repeats=2` is byte-identical to the canonical
Racket program. Production generator 2.0.0 and its authority remain unchanged.
The retained Python tiling loop is shared through `prototype.tile_output`;
`prototype.solve` keeps its original validation and API.

The alternative first selects the largest four-connected nonzero component by
occupied-cell count, treating adjacent different colors as one component. Ties
use the earliest actual occupied cell, not the bounding-box corner. It isolates
that component, preserves its colors, clears other components even inside its
bounding box, and crops the result. The retained color-selection, inversion and
tiling then consume that intermediate. A raw-bbox counterfactual changes a 30x30
qualified output while retaining its shape; skipping extraction changes another.

The raw grammar remains strict integer 0..9 grids with sides 1..15 and both zero
and nonzero cells. Solid derived frames are lawful and produce all-zero negative
tiles. A 30x30 input is excluded because the canonical 2x2 repeats would exceed
the 30x30 output bound. At maximum seed, the 15x15 stress input has 145 foreground
cells spanning all edges; 2x2 outputs have 320 input-frame or 376 component-frame
foreground cells, both with a 28x28 occupied span inside the 30x30 output.

Three constructive demos teach selection by pixels rather than bbox area,
four-neighbor mixed-color connectivity, isolation of interior clutter, actual-cell
tie order, and first-color semantics. The retained left-edge-last scan gap is
closed by different colors at columns 0 and 1 on the first occupied row of both
frames. A minimal 2x2 Racket regression changes the shortcut answer under all
eight settings. The input sampler retains all six demo/four-query roles before
prefixing and shuffling, uses separate local SHA streams, and matches inputs
across settings. Counts are 3..6 demos and 1..4 queries; seeds are 0..2**63-1.

Current verification: 72 focused tests including eight retained prototype tests;
392 core comparisons (384 demo-refuted, eight finite-consistent); 80 independent
comparisons (56 demo-refuted, 24 finite-consistent); no query conflicts or errors;
80 max-count/max-seed protected labels; 16 qualification jobs with 448 protected
evaluations; two replayed causal cases; 64 public one-query views and four rejected
corruptions. Consistent controls are inactive under the selected setting (unit
repeats or component selection under the input frame), not unresolved query
disagreements. This is finite evidence, not universal identifiability.

The native source inventory replaces the historical repeat-only inventory, whose
exact bytes are retained at `checks/11c53dabb028/retained-prototype-manifest.json`.
Current return evidence is under `checks/11c53dabb028/`: `audit/audit.json`,
`independent-rivals-v1/audit.json`, `qualification/`, `causal/`,
`left-edge-regression.json`, and `public-probe.json`. Earlier missing-dependency,
missing-feature and malformed-rival runs remain historical failures; their fixes
are exercised by the current results. No unrelated production battery was rerun.
The owner must qualify and freshly accept both exact integrated native builds.
No training data, mixture weights or training admission were changed.
