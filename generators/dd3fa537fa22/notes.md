# Working notes: dd3fa537fa22

## 2026-10-07 repair

Baseline v2.2.0 had eight mostly non-observable axes, no pinned `RULE_HASH`, and
required exactly two isolated cyan frames. That validator rejected canonical
`train[2]`, where one valid frame coexists with an insert-occluded incomplete
cyan candidate. Five of twelve inherited before-battery stages failed.

The replacement is constructive and retry-free. A single exact
`scene_profile` axis realizes four observable branches across canonical canvas
sizes. The parser accepts every canonical input, distinguishes complete from
incomplete cyan perimeters, mirrors the selected authority, rejects unknown
controls, and exposes semantic witnesses/rivals plus a lesson-identifiability
hook. Four demonstrations are required and the deterministic profile cycle puts
two crossed witnesses in every four-demo window.

A second shortcut review strengthened the crossed witnesses: their insert
shapes are always distinct transposes with equal area. This disproves both
`horizontal_order` and the stronger canonical-fitting
`area_then_horizontal` rival. Task-local tests enumerate all cyclic five-pair
windows and every query rotation; the independent workspace probe implements
its own parser and both rivals.

Known limits: generated normal scenes contain two inserts and at most two valid
frames; the selected authority can process more. The finite rival set does not
prove universal identifiability. Colors are fixed-role (cyan frames, arbitrary
non-cyan inserts), and the intentionally small four-profile curriculum favors
teaching clarity over exhaustive authority-domain coverage.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `df7eaa226d63f01ec9526b0ff6e20e495cb6404074257f3e290bd7cfd286222a`.

# Decisions — `dd3fa537fa22`

## D1: Pin and preserve the selected authority

**Choice.** Keep the selected Racket authority unchanged and declare
`RULE_HASH = "4ccb52845749"`. The output law is: start from zero, preserve only
complete cyan rectangular perimeters, fill each strict interior from a solid
non-cyan rectangle with the same ordered `(height, width)`, and clear all source
or invalid objects.

**Original rationale.** The imported v2.2.0 source did not state a rule hash and
its summary was looser than the selected authority, including uncertainty about
whether inserts remained. The exact historical rationale is unknown.

**Rejected alternatives.** Changing Racket/canonical data was unnecessary and
outside the defect. Retaining the old “inserts may be cleared or kept” summary
would leave labels underspecified. Matching rectangles by area alone was
rejected because orientation is semantically relevant.

**Probes and failure modes.** All four canonical input/output pairs are accepted
and mirrored; generated profiles are replayed through the selected Racket rule.
The hash pin will make future authority drift visible. Evidence:
`checks/reference-probe-v2.json` and the final battery's `authority_sync` stage.

## D2: Model complete frames and occluded candidates explicitly

**Choice.** Parse 4-connected foreground components into complete cyan
perimeters, solid non-cyan rectangles, and invalid cyan candidates. A candidate
whose missing perimeter cells are supplied by an overlapping solid insert is
recognized as the canonical occluded branch but is not preserved as a frame.

**Original rationale.** The baseline required exactly two isolated cyan frame
components. That simplification rejected canonical `train[2]`; why it was chosen
is not documented.

**Rejected alternatives.** Counting cyan components, accepting every cyan
bounding box as a frame, or patching only canonical `train[2]` by coordinates
would all encode incidental layout. Reconstructing the interrupted frame in the
output would contradict the authority.

**Probes and failure modes.** Canonical acceptance, structural mutation tests,
and the `occluded_frame_candidate` semantic witness cover this branch. Generated
normal scenes still cap the number of valid frames at two; this is a documented
distribution limit rather than an authority claim.

## D3: Replace dead axes with one exact observable axis

**Choice.** Expose only `scene_profile`, with four literal values. Difficulty
reorders allowed grid/shape choices but does not create hidden axis values.
Unknown keys, invalid profile names, invalid types, and invalid difficulty values
raise errors.

**Original rationale.** The old eight controls (`grid_h`, `grid_w`, palette,
density, texture, and related fields) were mostly not recoverable from generated
semantics. Their intended teaching rationale is unknown.

**Rejected alternatives.** Keeping no-op compatibility axes would make override
coverage look broader than it is. Exposing every low-level geometry decision as
an axis would expand the contract without adding a distinct rule branch.

**Probes and failure modes.** The final override stage checks 450 accepted cases
and strict rejection behavior. The trade-off is a deliberately small advertised
domain; consumers needing arbitrary object counts should expand the contract in
a later, separately tested revision.

## D4: Use four profiles and a deterministic teaching cycle

**Choice.** Cycle `aligned_frames_below`, `crossed_frames_below`,
`occluded_decoy`, and `crossed_frames_above` by `sample_index mod 4`.
`EXAMPLES_NEEDED = 4`; production lessons use four demonstrations and one query.
Thus every consecutive four-demo block contains all branches and two crossed
counterexamples.

**Original rationale.** The baseline had no explicit lesson-level teaching
schedule. Canonical layouts alone support positional shortcuts.

**Rejected alternatives.** Pure random profile selection can omit the only
counterexample from a lesson. Three demonstrations cannot guarantee all four
profiles. A single crossed profile leaves vertical placement correlated with
the rule witness.

**Probes and failure modes.** Tests enumerate schedule windows and held-out query
positions; the semantic gate checks 12 materialized lessons and 60 rotations;
the production census checks 300 lessons and 1,500 rotations. The cycle is
purposefully regular, so it favors reliable teaching over maximal layout
entropy.

## D5: Make the strongest canonical-fitting shortcut fail constructively

**Choice.** Crossed profiles draw only equal-area transposed pairs:
`(2×3, 3×2)` or `(3×4, 4×3)`. This makes ordered orientation necessary and
forces both `horizontal_order` and `area_then_horizontal` to disagree with the
authority. Non-crossed profiles may use five distinct shape pairs.

**Original rationale.** The first repair refuted plain horizontal pairing but
allowed crossed shapes with unequal areas. A stronger post-implementation audit
showed that “match by area, then resolve ties horizontally” still fit all
canonical examples and could survive those witnesses.

**Rejected alternatives.** The first area rival used nearest x-distance; tests
showed random spacing could accidentally recover the intended pairing, so that
model was rejected as too charitable. Merely adding more random spacing or
colors does not attack the area shortcut. The failed and corrected cycles are
retained in `checks/tdd-area-red.log`, `checks/tdd-area-green.log`, and
`checks/tdd-area-green2.log`.

**Probes and failure modes.** Both declared rivals independently fit 4/4
canonical pairs, then disagree on all 18 crossed rows in the independent probe
and 60/60 checked crossed witnesses in the semantic gate. This finite rival set
is not a universal uniqueness proof.

## D6: Preserve canonical scale while varying nuisance geometry

**Choice.** Reuse all four exact canonical canvas sizes
`11×13`, `12×14`, `13×15`, and `12×16`, with difficulty-dependent ordering only.
Use two distinct insert colors excluding background 0 and frame color 8. Randomly
distribute blank slack, vary vertical offsets, and optionally flip scenes
horizontally; one crossed profile also puts frames above inserts.

**Original rationale.** Exact old choices were generated through a retry loop;
the relationship between its nominal axes and resulting layouts was not clear.

**Rejected alternatives.** Assigning one canvas size per profile would leak the
profile from shape. Allowing frame color or background to vary would change
fixed semantic roles. Rejection sampling was replaced because it obscures
support and can silently bias rare branches.

**Probes and failure modes.** Construction is deterministic for
`(seed, sample_index, difficulty, overrides)`, leaves global RNG state untouched,
and passes purity/fresh-input tests. The chosen sizes and two-object layouts are
narrower than the full authority domain.

## D7: Reproduce the canonical occlusion branch directly

**Choice.** `occluded_decoy` contains one valid frame plus a second cyan
perimeter interrupted by an overlapping insert. The valid frame can still match
an insert; the incomplete candidate and all source inserts disappear.

**Original rationale.** This branch is visible in canonical `train[2]` but was
outside the baseline's validator and generator domain.

**Rejected alternatives.** A disconnected cyan decoy would not reproduce the
same parser challenge. A complete unmatched frame would be preserved by the
authority and therefore test a different law.

**Probes and failure modes.** The profile has a dedicated structural test and
fired 147/600 times across every difficulty band in the final semantic gate.
Generated occlusion is representative, not exhaustive of every possible overlap.

## D8: Keep independent oracles and exact lesson contracts

**Choice.** Add task-local tests plus `workspace/reference_probe.py`, whose
component parser, authority mirror, and rivals do not call generator parsing or
output helpers. Declare semantic witnesses, canonical shortcuts, lesson
competitors, and a `lesson_identifiable` hook in the generator.

**Original rationale.** The baseline had no semantic contract and therefore
received only an advisory from the semantic gate.

**Rejected alternatives.** Testing generator output against its own mirror alone
would permit shared bugs. Relying only on canonical labels would not test
teaching ambiguity. A single ordered-production check would not establish that
held-out query positions are safe.

**Probes and failure modes.** The staged and fresh suites each pass 31 tests;
the independent probe checks canonical and generated cases; the required
rotation census finds no ambiguity against the declared rivals. New plausible
rivals should be added to both the independent probe and lesson contract before
claiming broader identifiability.

## D9: Preserve solve isolation and replay the exact handoff

**Choice.** Complete the assigned blind task before repair inspection; after the
repair, run a new visible-only solve marked with prior exposure `yes` and
reference consultation `no`. Generate an exact patch from the immutable packet,
apply-check and apply it in an isolated fresh extraction, compare source hashes,
and rerun focused tests there.

**Original rationale.** This follows the packet's isolation and maintainer
handoff contract.

**Rejected alternatives.** Reusing the pre-strengthening solve would bind the
record to stale generator bytes. Testing only the working directory would not
catch omitted files or a malformed patch.

**Probes and failure modes.** `solve/summary.json` is bound to the final generator
SHA; `checks/prior-solve/` preserves the superseded solve; and
`checks/fresh-replay-verification.json` records the successful fresh replay.
No Racket authority or canonical data was changed.
