# Current notes: 0a7f0faace31

## Intended rule and authority

Background is 5. Form the inclusive bounding box of every 7. Enumerate
monochrome four-connected components of colors other than 5 and 7 in row-major
discovery order. Select the first component whose inclusive-bbox center,
`floor((min + max) / 2)` on each axis, lies inside the guide bbox. Return the raw
bbox subgrid, preserving background, foreign colors and guide cells inside it.
Missing guide cells or an eligible object are outside the generated domain.

The canonical Racket rule is unchanged and remains the label authority.
`RULE_HASH=b5a68207c8ed`; authority-set SHA-256 `f2de636d5a111718a93f662b73420725e578a4e5ba1ddc6c9a62cd26dc539507`. Python mirrors and
rivals are authoring diagnostics only.

## Current source

Version `3.0.4`; generator SHA-256 `c9985a30b4ea46dd497b57229a9c8ffa92e7f866c968afe55495a97a89874862`. This assignment used the prior
selected-task notes/counterexample from `review-25485a577009d7e1` only as a lead
and remeasured the supplied baseline `48efc388363dec9a69e0ac82dca3fbddc25b049255e9d39ea6dfad9714c9b13e`.

Current repairs:

1. `seed` and `sample_index` must be exact Python integers; booleans, floats and
   strings are rejected, and sample indices must be nonnegative.
2. The default schedule still repeats `teaching, teaching, ordinary`. The first
   ordinary position in each nine-sample block is a reproducible `plain` board.
   Plain boards use five distinct nonzero glyph colors (selected plus four
   outside distractors), matching the shared canonical-training palette-role
   signature `(2 preserved, 0 added, 5 removed)`. Other ordinary positions keep
   stochastic textures and the broader palette, including color 0.

The palette change is distribution-only. It does not alter selection or output
semantics. A documentation-only comment correction from “four removed” to
“five removed” changed the final source hash; all final source-bound evidence
and the exposed solve were rerun. The earlier solve is retained under
`checks/pre-comment-freeze-8329542f.../`.

## Controls and curriculum

Exact grid height/width controls are integers 12..24. Frame styles are
`corners`, `dashed`, `full`, and `two_corners`; textures are `plain`,
`multi_inside`, `center_out`, `sticks_out`, and `teaching`. A full frame is
explicitly incompatible with the three crossing textures (`center_out`,
`sticks_out`, `teaching`). Unknown axes and invalid enum/scalar values fail
closed.

The compound teaching board deliberately includes multiple eligible and
near-eligible components, repeated disconnected colors, diagonal contact,
center-rounding boundaries, foreign pixels in crops, and size/width/sparsity
competitors. Eighteen declared rivals cover containment, overlap, rounding,
connectivity, color grouping, masking, ordering and object-choice shortcuts.
Three demonstrations are required.

## Proposed parameterization

A task-local prototype under `workspace/parametric/` varies one episode-level
parameter: `selection_order=first|last`. `first` materializes the exact canonical
program; `last` reverses only the eligible list at the selection site. One
Racket-backed four-pair episode per setting is retained, and every query rotation
leaves a demonstration that refutes the alternate value. This is proposed only;
it does not change production generation, authority or approval state.

## Final evidence

- 12/12 final battery stages green; standalone lint green.
- 213/213 portable task tests pass.
- Profile floor: exact 34/60; canonical envelope 44/60.
- Semantic gate: strict 600/600; 12/12 smoke lessons; 0/48 diagnostic rotations ambiguous.
- Override matrix: 41,310 draws, 41,040 accepted, 270 declared incompatibility rejections, zero findings.
- Lesson census: 300/300 materialized (100 per band), three demonstrations plus one query, 1,200 unique inputs, zero production ambiguity/errors/warnings, and zero ambiguity/errors/warnings over all 1,200 held-out query rotations.

Decisive paths are `checks/after-final/`, `checks/task-tests-final/`,
`checks/lesson-census-final.summary.json`, and `checks/parametric/evidence.json`.

## Limits and open findings

These are finite checks against declared and searched rivals, not a proof of
unique induction. The random census uses consecutive requested starts and does
not exhaust every seed or cyclic start. Teaching geometry is intentionally
structured; ordinary slots provide broader shape and size support. The
prototype covers two settings and one episode each. The selected repair has no
known blocker, but passing checks do not grant training admission or approve the
proposed alternate rule.
## Current reviewer considerations

Source SHA-256: `c9985a30b4ea46dd497b57229a9c8ffa92e7f866c968afe55495a97a89874862`.

# Decisions: 0a7f0faace31

Final generator version `3.0.4`, SHA-256 `c9985a30b4ea46dd497b57229a9c8ffa92e7f866c968afe55495a97a89874862`. Finding IDs match
`REVIEW.md`. The canonical Racket authority and short rule pin `b5a68207c8ed`
were not changed.

## D1 / R1 — Enforce exact call scalars at the public boundary

**Prior choice and rationale.** The baseline accepted values that Python treats
as integer-like, including booleans and integral floats. No rationale was
recorded; the most likely explanation is that validation focused on declared
overrides rather than the positional call arguments.

**Decision.** Require `type(seed) is int`, `type(sample_index) is int`, and a
nonnegative sample index. Reject rather than coerce. This follows the rest of
the generator's fail-closed exact-control contract and prevents semantically
different calls from silently sharing RNG streams.

**Alternatives rejected.** `isinstance(..., int)` would still accept booleans.
`int(value)` coercion would accept strings and truncate floats. Leaving the
contract permissive would keep strict defect lint red.

**Probe and limits.** Focused tests first failed on booleans, floats, strings and
negative indices (`checks/contract-hardening-red.log`) and now pass in the
213-test portable stage. This change does not validate arbitrary-size integer
magnitude; deterministic RNG handling remains the runtime's responsibility.

## D2 / R2 — Add bounded canonical-training palette-role support without flattening diversity

**Prior choice and rationale.** Ordinary boards sampled colors from a palette
including zero and placed one to three exterior distractors. That maximized
variety but did not guarantee overlap with the shared detector's canonical
training signature in its first eight draws. The original rationale for leaving
that support probabilistic is unknown.

**Decision.** Keep the broad palette for most textures. For the first ordinary
slot in each nine-sample block (`sample_index % 9 == 2`), choose `plain` and use
five distinct nonzero glyph colors: one selected component plus four exterior
distractors. Require all four placements to succeed before accepting the board.
Under the detector's zero-ignoring definition this yields
`(preserved, added, removed)=(2,0,5)`, matching both canonical training pairs.

**Alternatives rejected.** Changing the shared diagnostic to count zero would
alter policy for every task and would not address its training-only support
contract. Forcing every ordinary board to this palette would unnecessarily
reduce texture diversity. Altering compound teaching boards risked coupling a
structural-lint repair to the semantic witness. Matching the labeled canonical
test signature `(2,0,4)` was also rejected after the final probe established
that defect lint calibrates on training pairs only.

**Probe history and failure modes.** The first regression incorrectly counted
zero; the second included the canonical test pair. Both honest failures are
retained in `checks/contract-hardening-palette-*.log` and
`checks/contract-hardening-train-palette-red.log`. The final regression mirrors
`review_diagnostics.py`. This is bounded support, not a claim that every draw
matches canonical color-role counts. Plain placement may retry, but remains
bounded by the existing ordinary-grid attempt loop.

## D3 — Preserve the canonical rule and authority

The canonical behavior remains: find the inclusive bbox of all 7s, enumerate
monochrome four-connected non-5/7 components in row-major discovery order,
select the first whose floored bbox center lies inside the guide, and return its
raw bbox crop. Neither the Racket program nor canonical examples needed repair.
Changing the rule to accommodate distribution diagnostics was rejected. Final
authority-set SHA-256 is `f2de636d5a111718a93f662b73420725e578a4e5ba1ddc6c9a62cd26dc539507`; execution parity remains green.

## D4 / P1 — Prototype one meaningful rule parameter in isolation

**Choice.** `selection_order=first|last`, selected once per episode. It changes
the executed decision while preserving guide construction, component roles,
connectivity, center test and raw-crop transformation. `first` is byte-for-byte
the canonical program; `last` reverses only the eligible list at the selection
site.

**Alternatives.** Cosmetic palette/size parameters were rejected because they do
not change the rule. A widest-object parameter is plausible but combines
selection order with a size objective and tie behavior. First/last is the
smallest interpretable neighboring rule and directly exposes a canonical
ambiguity.

**Evidence and limits.** Two Racket-backed four-pair episodes, one per setting,
are in `checks/parametric/evidence.json`; every query rotation is distinguished.
The prototype remains under task-local `workspace/parametric/` and does not
change the production API, authority, catalog approval or training admission.
One episode per setting is bounded evidence, not full parameter-space coverage.

## D5 — Retain the existing teaching schedule; measure both production and rotations

The current default profile remains `teaching, teaching, ordinary` by sample
index, with three demonstrations and one query in lesson assembly. A source-bound
100-per-band census was preferred over inventing new rival geometry because the
existing compound teacher already refutes all 18 declared canonical-fitting
rivals. The census uses consecutive requested starts and holds out each of four
materialized pairs once. It found zero ambiguity among 300 production lessons
and 1,200 rotations. This does not enumerate all seeds, all schedule starts or
undeclared rules.

## D6 — Correct a documentation-only source mismatch and rebind evidence

During handoff writing, an inline comment was found to say "four removed" while
the measured canonical **training** signature and regression are "five
removed." The comment alone was corrected. The prior source-bound solve and
compact receipts at SHA-256
`8329542f159ed4a6c5fc87f7c8524e53dfc4eef4f076da345ba238abd0fdb6b7`
are retained under `checks/pre-comment-freeze-.../`; all final task tests,
battery, census, prototype materialization, shortcut probe and exposed solve
were rerun under `c9985a30b4ea46dd497b57229a9c8ffa92e7f866c968afe55495a97a89874862`. No executable statement changed.
