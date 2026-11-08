# c78d339cf2f2: exposed-edge perimeter ranking

## Current rule and authority

Version 2.0.0 generates inputs for the unchanged canonical Racket rule, pinned by
`RULE_HASH = "ea2222b6763c"`. Find spatial 4-connected components of **any nonzero
colors**, count exposed unit edges (including hole boundaries), sort by increasing
perimeter, and recolor the three components 2, 3, 4. Equal perimeters retain
row-major component discovery order. Input color does not determine output rank.

The intended input domain is a rectangular ARC grid with background 0 and exactly
three spatial components. The validator accepts multicolor bodies and true ties;
the production sampler uses one shared foreground color. More than three bodies
would be truncated by the authority's three-color loop and is outside this domain.

## Reversed distribution decisions

The imported 1.1.1 summary required three distinct input colors and distinct
bounding-box perimeters. Its historical rationale is unknown: the working notes
were a placeholder. That validator rejected all five canonical inputs and its
default sampler had zero exact/envelope profile hits in the 60-draw before gate.
Bounding-box perimeter also concealed the actual unit-edge rule.

The new sampler uses a finite bank of connected oriented 3x3 subsets plus vertical
length-4/5 lines. Ordered metric profiles force exposed-edge ranks to differ from
area, bounding-box perimeter, bounding-box area, and row-major order; placement
also refutes column-major order. Cached data are immutable geometry, never samples.
Random disjoint slots have a constructive fallback on every advertised canvas.

Only actual exact controls are advertised: height 8..20, width 12..20, foreground
1..9. Each supports all values in every difficulty band, jointly at the tested
boundaries. Canonical dimensions and foreground 6 receive extra probability;
difficulty changes shape-area weights. Removed placeholder controls fail clearly.
Booleans, coercible strings/floats, invalid primary arguments, and unknown controls
are rejected. `None` for an optional override retains default sampling.

## Teaching contract

Use three demonstrations and one query from four consecutive sample indices.
Even indices have a perimeter tie and odd indices have three distinct perimeters.
Every such window therefore has two of each; holding out any one pair still leaves
a tie example. The executable lesson hook tests actual demonstration fits and query
disagreement for seven declared rivals. Area and bounding-box perimeter are the two
rivals verified to fit all five canonical pairs.

Final-source evidence in return `review-12c58f2029db2de8`: 12/12 battery stages;
canonical inputs accepted 5/5; profile floor 26/60 exact and 33/60 envelope; semantic
strict support 339/600; 300 production lessons and 1,200 query rotations with no
declared-rival ambiguity. The period-2 census covers six starts and 24 rotations at
fixed seed 0 across all bands. These finite checks do not certify undeclared rules.
Focused tests and the seed-23 authoring counterexamples cover the changed behavior.

## Limits and proposed extension

The finite shape family and deliberate metric disagreements are distribution
restrictions; this is not an exhaustive sampler of arbitrary connected shapes.
The validator accepts a broader lawful domain than the default sampler visits.
No claim is made about nonconsecutive lesson assembly, fewer demonstrations, all
random seeds, or universal rule identifiability. The ascending/descending rank-order
extension in `workspace/parametric/` is an authoring prototype; it does not change
the selected rule, generator API, approval status, or training admission.

Detailed choices, failures, exact commands and hashes are in the return's
`DECISIONS.md`, `REVIEW.md`, `RESULTS.json`, and `checks/`. Original associated notes
remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `cbdd4947abe1da3e9309c83fbd44104099bc36da6701075a43d0c93deba1c534`.

# Decisions for review-12c58f2029db2de8

## Scope and source identity

Selected task: `c78d339cf2f2`, version 1.1.1 → 2.0.0. The original generator hash is
`8887f17d6a6e3fdb44a494629e28f9b2325f5feb17e4e9f52e3eff6cacd05dcb`;
the final generator hash is
`cbdd4947abe1da3e9309c83fbd44104099bc36da6701075a43d0c93deba1c534`.
The canonical Racket authority is unchanged, full rule-text SHA-256
`ea2222b6763c9e504ccce7e1d84a4377a62ea86e64ed1e97bf5615d9145b0692`.
Task source edits stay under the selected generator directory. The two audit
targets are findings only. Shared code, frozen fixtures, the draw, wrapper, runtime,
catalog, and canonical data were not edited.

The imported notes supplied no substantive rationale. Statements below about why
the previous author chose a distribution are therefore unknown, not reconstructed
intent. Original associated notes remain intact.

## D1 / G1: use the actual component and perimeter semantics

The old description and sampling policy used three distinct colors and distinct
bounding-box perimeters. The authority instead groups adjacent nonzero cells
regardless of color and measures exposed unit edges, including holes. All five
canonical inputs use foreground 6 on background 0, and canonical examples contain
true perimeter ties. The previous validator rejected all five canonical inputs.

The new validator counts spatial components and checks rectangular integer ARC
grids, background 0, and exactly three components. Exactly three is meaningful:
the authority pairs components with only three output colors. It accepts mixed
colors within a component and tied perimeters; it does not impose the sampler's
small-shape limits on the whole lawful domain. Area and bounding-box perimeter
each fit all five canonical labeled pairs, so canonical agreement alone does not
teach which metric to use. Focused regressions independently flood-fill bodies
and compute perimeter as `4 * area - 2 * shared_internal_edges`.

Rejected alternative: changing the Racket rule to bounding-box perimeter or
requiring distinct true perimeters would erase observed canonical behavior.
Rejected alternative: retaining three colors as object identity would preserve
the false validator and introduce an avoidable color cue.

Evidence: `checks/before/`, `checks/commands/regression-red.log`,
`checks/after-final/`, and task `tests/test_rank_generation.py`.

## D2 / G2: make metric counterexamples routine

The generator enumerates normalized connected oriented subsets of a 3x3 canvas
with at least two cells, plus vertical length-4 and length-5 lines. It groups them
by perimeter, area, bounding-box perimeter and bounding-box area. Profile selection
requires perimeter order to disagree with all three alternative metric orders and
row-major order. A spatial placement condition also refutes column-major order.
The bank is finite and cached; samples and mutable output grids are not cached.

This creates exact teaching witnesses without unbounded rejection. The extra
vertical line family includes the canonical length-4 line while keeping every
shape within three columns. Three disjoint equal-size slots, with a constructive
fallback, fit the smallest 8x12 canvas. A single shared foreground color prevents
input color from distinguishing ranks. This choice is about teaching support;
foreground 2, 3, or 4 is legal even when it happens to equal an output color.

Rejected alternative: unrestricted random walks are broader but gave no simple
guarantee that a short lesson refutes the canonical-fitting metrics. Rejected
alternative: rejecting whole generated lessons until they happen to work adds
sampling cost and obscures the support of exact overrides. A broader bank can be a
future change with the same executable contract; it is not claimed here.

New restriction self-review: every default input deliberately contains a metric
disagreement, and the geometric bank is finite, so this is not a representative
sample of every lawful shape relationship. Seven explicit rivals, two real-Racket
seed-23 counterexamples, and the source-bound censuses cover the stated teaching
claim; arbitrary unseen hypotheses remain untested.

Evidence: selected `counterexamples/`, `workspace/reproduce_counterexamples.py`,
`checks/counterexamples/`, and final census reports.

## D3 / G3: honest support and exact controls

The public exact axes are height 8..20, width 12..20 and foreground 1..9. Each
advertised value has positive default weight, supports literal-integer overrides
in every difficulty band, and is observable from the generated grid. Height 8..10,
width 12..13, and foreground 6 receive extra weight to recover canonical profile
support without restricting generation to those profiles. Easy and hard bias
total shape area; difficulty does not secretly narrow the exact axis domains.

The final fixed profile-floor probe produced 26 exact and 33 envelope hits out of
60 draws, with exact support 11/20 easy, 7/20 medium and 8/20 hard. Canonical input
acceptance changed from 0/5 to 5/5. A separate semantic draw set measured strict
support 339/600, above the declared floor of 0.25. These are distinct samples and
definitions; they must not be combined into one denominator.

Unknown axes fail, and obsolete placeholder axes were removed. Primary seed,
sample index and difficulty arguments and numeric overrides reject booleans and
coercible nonliteral types. `None` on an optional override retains the default.
All tested joint minimum/maximum combinations are realizable. No incompatible
axis pairs are declared because the constructive placement supports the complete
advertised canvas bounds.

Rejected alternative: keeping ignored axes for interface appearance would retain
misleading controls. Rejected alternative: allowing difficulty-specific override
subranges would make the declared control domain false.

The first repaired battery exposed a real remaining defect in strict validation
of primary call arguments: 11/12 stages passed and defect lint failed. Added three
parameterized regression cases first reproduced it, then the explicit validation
fix passed. Both runs remain in `checks/after/` and `checks/commands/scalar-red.log`.
Final evidence is `checks/after-final/`; intermediate successes are not rebound
to the final hash.

## D4 / G4: a lesson contract that survives permitted rotations

Production assembly uses **three demonstrations and one query**, four consecutive
sample indices. Even indices have exactly two distinct perimeter values (one tied
pair); odd indices have three. Every four-pair window has two tied and two distinct
inputs. Holding out any single pair retains at least one tie demonstration.
Every individual input already refutes the area, bounding-box, and scan-order
rivals. The hook checks actual rival fits on labeled demonstrations and actual
query disagreement; it does not simply assert the curriculum is identifiable.

Seven declared rivals are tested: area, bounding-box perimeter, bounding-box area,
row-major, column-major, descending, and reversed equal-perimeter ties. Only the
first two are declared canonical shortcuts because only those fit all five
canonical pairs. The production and all held-out-pair rotation policies are both
required, preserving original relative demonstration order after each holdout.

Final hash: 300 lessons (100 per easy/medium/hard band), 1,200 unique inputs, and
1,200 rotations, with zero ambiguity, hook warning, materialization error or
scoring error. The separate period-2 census exhausts both start residues in all
three bands at fixed seed 0: six lessons and 24 rotations, with 14 unique inputs
because these small windows overlap. This exhausts declared residues at that seed,
not all seeds or all possible rules. Fewer than three demonstrations or arbitrary
nonconsecutive lesson assembly has not been certified.

Evidence: `checks/lesson-census-final.json`, its summary, and
`checks/schedule-census-final.json`. The smaller semantic gate independently
materialized 12 lessons and 48 rotations with required rotation policy.

## D5 / P1: proposed rule-parameter extension

Status: **runnable authoring prototype; proposed, not production-approved**.
The suitable parameter is `rank_order = ascending | descending`, chosen once per
episode. Palette 2,3,4, spatial any-nonzero connectivity, exposed-edge perimeter,
and stable tie order stay fixed. The default uses the exact canonical program
text; the alternative changes the comparison direction. Varying output palette
was considered but omitted: it adds a second inference burden without being
needed to demonstrate useful rule parameterization. Parameters that changed the
number of bodies would conflict with the fixed three-color authority.

`workspace/parametric/prototype.py` independently samples witnesses, instantiates
matching Racket programs and checks both settings against demonstrations. Public
JSON contains only train input/output and query inputs; parameters, seeds, program
text, metadata, and query outputs remain in authoring evidence. It does not replace
or wrap the selected production generator.

Measured seeds 0..7: eight episodes (five ascending, three descending), 24
demonstrations, 16 queries, 98 real Racket evaluations, 48 parameter/demo checks,
zero ambiguous generated episodes. The default reproduced all five canonical
pairs. A same-input counterfactual changed 12 cells between settings; an intentional
ambiguous control correctly retained both settings. Fifteen focused tests passed.
The independent sampler uses only three small shape triplets on 19..22 canvases;
this is finite prototype evidence, not universal family support.

Canonical/ascending program hash:
`ea2222b6763c9e504ccce7e1d84a4377a62ea86e64ed1e97bf5615d9145b0692`.
Descending program hash:
`e22e20880ac0ae23864573cc2a4902a07a29438a90fe58cdc1c4782db703f214`.
Exact callable hashes, settings, files and commands are in
`checks/parametric/evidence/manifest.json`, `checks/parametric/commands.json`, and
`checks/parametric/artifact-integrity.json`. An initial namespace import failure
and the expected missing-prototype test failure are retained as genuine attempts.

## D6: exposure and evidence handling

The separate task `00ed2544a15e` was solved before opening task-specific repair or
audit references. Its exposure declaration and all actual attempts stay in
`solve-blind/`. The later selected-task solve is explicitly exposed because the
rule was reviewed during repair; during that solve only public challenge data and
Python experiments are used. Neither episode's hidden query correctness is claimed.

Large intermediate evidence is retained losslessly with original-path, byte-count
and SHA-256 mappings plus restoration instructions. Final source-bound reports,
failed attempts, and actual command receipts remain distinguishable. The passive
receipt helper checks records and optional explicit source hashes; semantic
approval and command reexecution remain separate operations.
