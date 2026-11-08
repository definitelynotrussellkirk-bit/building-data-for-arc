# Working notes: db98b701e5bb

## Intended rule

Find the 4-connected color-2 components. Recolor the unique component with the
largest **cell count** to color 8. Preserve all other cells. The pinned canonical
rule hash is `da19a5612a17`.

## Final design (`VERSION = 3.1.0`)

- Inputs use canonical-size three-color profiles by default: 8–10 rows and
  10–13 columns, two to four separated red components, and one connected
  non-{0,2,8} distractor.
- The maximum red size is unique; smaller sizes may tie. This intentionally
  accepts the canonical `(3,3,5)` profile that the old validator rejected.
- Four advertised controls are real and exact: `grid_h`, `grid_w`,
  `component_profile`, and `distractor_color`. Unknown, retired, mistyped, or
  out-of-domain overrides are rejected.
- Placement is constructive, not rejection/fallback based. An 8×8 zone layout
  keeps red components separated even diagonally and reserves legal space for
  the distractor.
- The default three-index lesson schedule rotates the true largest object
  through scan ranks 0, 1, and 2. Residues 1 and 2 also place size-4 and size-5
  objects in equal-area bounding boxes, with size 4 earlier, refuting the
  strongest canonical-fitting shortcut: “choose maximum bounding-box area,
  then earliest in scan order.” Thus each three consecutive examples contains
  two bounding-box counterexamples, and each one-query rotation of four
  consecutive pairs leaves at least one.
- Executable rivals are first red, last red, smallest red, and largest
  bounding-box area. `lesson_identifiable` checks the declarations directly.

## Reversed decisions

The imported `2.2.0` generator required all red sizes to be strictly distinct,
advertised several dead controls (`palette_kind`, `texture`, `anchor_corner`,
`asymmetry_force`), silently ignored unknown overrides, and allowed random
fallbacks to obscure the requested contract. The replacement permits lawful
smaller ties, removes controls that do not express the rule, rejects unknown
keys, and makes every retained control observable. Evidence: the before battery
under `checks/before/`, the retained prior audit in
`counterexamples/review-70634d10d5e597b9-v0001/`, and final focused tests.

The active archived Racket `target_code` differed from canonical `raw_code`
only by a comment. Because the assignment explicitly allowed authority repair,
that selected authority field was synchronized byte-for-byte; behavior and rule
hash remain unchanged.

## Evidence and limits

- `tests/test_generator.py`: 62 focused tests covering canonical examples,
  controls, validators, schedule/rotation guarantees, RNG purity, and rivals.
- `workspace/reference_probe.py` and `workspace/reference-probe.json`: an
  independent Python oracle; 256 samples per band, 768/768 valid and distinct,
  all canonical profiles represented, and all scheduled scan ranks observed.
- `counterexamples/largest_bbox_area.json`: exact final-generator shortcut
  counterexample, independently mirrored and confirmed by the selected Racket
  rule in `checks/shortcut-counterexample-final/racket.json`.
- `checks/lesson-census-v31-final.json`: 300 production lessons, 1,200 unique
  inputs, and 1,200 query rotations; no ambiguity against declared rivals.

These are finite checks against named rivals, not a proof of unique induction
against every imaginable rule. The production guarantee is for normal
consecutive sample-index lessons (and their one-query rotations); arbitrary
hand-picked nonconsecutive triples are outside that schedule guarantee. Shapes
and size profiles are deliberately finite, and difficulty changes canvas-profile
weights rather than the semantic transformation.
## Current reviewer considerations

Source SHA-256: `df383b326e616db37d3cc21d9337aafc165d19c9109d7e37a3a1cdb05fc57ff2`.

# Decisions — db98b701e5bb

## D1 — Bind the implementation to the canonical rule

**Input/lead.** The assignment pinned rule hash `da19a5612a17`; the imported
source omitted `RULE_HASH`, while rule smoke itself passed.

**Decision.** Declare the exact rule hash and treat the Racket rule as fixed:
select the unique largest color-2 4-component by cell count and recolor it to 8.

**Alternatives rejected.** Editing semantics to require all sizes distinct, or
choosing by geometric extent. Both contradict canonical evidence.

**Probe/failure mode.** All five canonical inputs are accepted and independently
recomputed in focused tests and `workspace/reference-probe.json`. Rule drift is
caught by lint, rule smoke, authority sync, and the source-bound task tests.

## D2 — Permit smaller-size ties

**Prior choice.** Version 2.2.0 required all red component sizes to be strictly
distinct.

**New choice.** Only the maximum must be unique. Profiles include `(3,3,5)`.

**Reason/evidence.** A canonical training input has two size-3 components and a
size-5 target. The old `self_check` rejected its own authority example.

**Failure mode covered.** A tie for the maximum remains invalid and is tested;
smaller ties are lawful.

## D3 — Replace dead axes with four honest exact controls

**Prior choice.** `palette_kind`, `texture`, `anchor_corner`, and
`asymmetry_force` were advertised but ignored; unknown keys were also silently
accepted. The retained prior audit reproduced 120/120 identical opposing values
per dead axis.

**New choice.** Advertise only `grid_h`, `grid_w`, `component_profile`, and
`distractor_color`; reject unknown/retired, mistyped, or invalid values before
construction. Each accepted override round-trips through an independent
observer.

**Alternative rejected.** Implementing decorative controls merely to preserve
an old API. They do not teach the transformation and expand joint-contract risk.

**Probe/failure mode.** Focused tests enumerate every value across all three
bands; the final override battery independently probes exactness.

## D4 — Construct placements instead of retrying/falling back

**Decision.** Place red objects in separated 3×3 zones inside an 8×8 block and
choose the distractor from all cells outside a one-cell red halo.

**Reason.** This proves separation and avoids an override being silently changed
after random placement failure.

**Alternative rejected.** Unbounded rejection sampling or fallback to an easier
profile. Those make seeds fragile and can violate exact controls.

**Limits.** Supported shapes are finite and fit 3×3 zones; dimensions are
8–10 by 10–13. These are intentional generator-domain limits.

## D5 — Match canonical dimensions by default

**Decision.** Difficulty bands weight canonical profiles `(8,10)`, `(8,11)`,
`(9,12)`, and `(10,13)` rather than inventing larger canvases.

**Reason/evidence.** The old source failed the profile-floor check. The final
independent probe records a canonical-size/palette hit for every one of 768
generated samples; the official profile-floor stage passes.

**Limit.** Difficulty affects canvas weighting, not rule complexity.

## D6 — Make the lesson schedule refute positional rules

**Decision.** For default consecutive indices, rotate the true largest object's
scan rank through 0, 1, and 2.

**Reason.** Without controlled order, “first red” or “last red” can fit an entire
lesson despite every label being correct.

**Probe.** Exhaustive task tests cover cyclic three-example windows and every
one-query rotation of four consecutive examples.

## D7 — Add a stronger canonical-fitting geometric rival

**Discovery.** After the official battery was green, an independent probe found
that “maximum bounding-box area, scan-order tie break” fit all five canonical
pairs. The pre-fix schedule could leave complete lessons ambiguous.

**Decision.** Declare that rival executable and make residues 1 and 2 place an
earlier size-4 and true size-5 object with equal bounding-box area 6. A normal
three-example lesson has two refutations; any one-query rotation of four
consecutive examples leaves at least one.

**Alternatives rejected.** Merely documenting the shortcut, relying on rare
random witnesses, or deleting the rival from the contract.

**Evidence.** `counterexamples/largest_bbox_area.json`, supported Racket receipt
`checks/shortcut-counterexample-final/racket.json`, 62 focused tests, and the
300-lesson / 1,200-rotation final census.

**Limit.** The contract tests four named rivals. It does not establish universal
identifiability against all programs or arbitrary nonconsecutive hand-picked
triples.

## D8 — Synchronize comment-only Racket authority text

**Observation.** The selected archived `racket_target.target_code` differed from
canonical `raw_code` only by a comment, causing defect-lint/authority-sync
failure despite equal behavior.

**Decision.** Because `shared_authority_write_allowed` was true, copy the exact
canonical source into the selected active authority field. Do not alter the rule.

**Probe.** Rule hash remains `da19a5612a17`; rule smoke, Racket lint, and
authority sync pass on the final source.

## D9 — Add portable, independent tooling

**Decision.** Retain `workspace/reference_probe.py` and source-bound tests that
load the generator by path, use `reviewer_support` for canonical pairs, and
implement their own component/oracle logic.

**Reason.** Reusing generator helpers would let the same defect validate itself.
The tool also reports diversity, canonical-profile support, scan ranks, and rival
disagreement counts for future agents.
