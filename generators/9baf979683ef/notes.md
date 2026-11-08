# Working notes: 9baf979683ef

## Review identity

- Assignment: `review-ba64e5e4135b362e`
- Baseline generator SHA-256: `8c8f45332e5fe7119ea2ea95ee34214923ddf55c9b010da11920e9b96c5cb015`
- Final generator SHA-256: `29f83f4da2ccb13bfc121f6497a76461a39f7c8adf89abff5802d400d2ac71a5`
- Canonical rule hash: `1fce392f92a1`
- Reference authority changed: no

## Root cause

The imported v2.1.0 generator exposed nine axes but did not implement several
of them (`palette_kind`, `palette_size`, `position_bias`,
`n_distinct_colors`, and `density`), silently accepted unknown keys, and
mutated requested dimensions (for example, even widths were incremented).
Its validator also treated deliberately invalid textures as advertised
production controls. The completed before battery was therefore only 7 green,
2 advisory, and 3 failed; the override stage recorded large classes of
mismatches and rejected declared cases.

The canonical examples also share two accidental regularities: the divider is
always the geometric midpoint and there are exactly five source cells. Both
shortcut programs fit all 3/3 canonical pairs, so merely diversifying colours
or positions would still leave weak lessons.

## Selected repair

Version 3.0.0 replaces the false interface with five exact, directly observable
controls:

- `profile_kind`: three canonical and two expanded shapes;
- `divider_side`: one column left or right of the midpoint;
- `source_scale`: six, seven, or eight source cells;
- `source_palette`: one through four source colours;
- `layout_kind`: connected, scattered, or mixed geometry.

Unknown controls are rejected. `observe_overrides()` reconstructs all five
values from a returned grid, and `self_check(..., meta={"overrides": ...})`
verifies requested values. The independent `rule_mirror()` oracle is used only
for tests and semantic probes; Racket remains output authority.

Production scenes deliberately combine an off-centre divider with more than
five sources, so each individual scene refutes both canonical-fitting
shortcuts. Shapes and palette profiles remain close to canonical data, while
source topology and difficulty-weighted source count add useful variation.

## Verification

Final-source evidence is bound to generator hash
`29f83f4da2ccb13bfc121f6497a76461a39f7c8adf89abff5802d400d2ac71a5`:

- Full after battery: 12/12 green, 0 advisory, 0 failed
  (`checks/after-complete/checks/9baf979683ef_after_battery_summary.json`).
- Selected task tests: 9/9 passed
  (`checks/task-tests-final/result.json`).
- Profile floor: all 3 canonical inputs accepted; 26/60 draws hit an exact
  canonical size/palette profile, with support in every band
  (`checks/after-complete/checks/9baf979683ef_after_profile_floor.json`).
- Semantic gate: 600/600 strict draws, all required witnesses and rival claims,
  and 12/12 smoke lessons passed
  (`checks/after-complete/checks/9baf979683ef_after_semantic_gate.json`).
- Lesson census: 100/100 lessons materialized per band, 1,200 exact unique
  inputs across all lesson pairs, 0 ambiguous lessons, 0 hook warnings, and 0
  scoring errors; every declared rival was refuted in every lesson
  (`checks/lesson-census-final.json`).
- Task-local cyclic audit: 300 sampled scenes were valid and unique, and all
  1,200 cyclic query rotations were identifiable against the declared rivals
  (`checks/task-local-audit-final.json`).

## Limitations and self-review

The distribution intentionally omits centred-divider and exactly-five-source
production scenes. This is a teaching choice to break canonical shortcuts, not
a statement that those inputs are outside the true rule domain; all canonical
inputs still pass the validator and oracle. The retained canonical profile
weights mitigate morphology drift, but the production distribution therefore
leans toward counterexamples more heavily than the three public examples.

The rival audit is finite and declaration-based. It establishes that the two
known canonical-fitting shortcuts do not survive the measured lessons; it does
not prove universal identifiability or rule out undeclared semantic rivals.
Exact grid hashes measure byte-level uniqueness rather than semantic distance.
## Current reviewer considerations

Source SHA-256: `29f83f4da2ccb13bfc121f6497a76461a39f7c8adf89abff5802d400d2ac71a5`.

# Decisions — `9baf979683ef`

## D1: Preserve the authoritative transformation

**Decision.** Keep the canonical Racket program and all canonical examples
unchanged. Pin `RULE_HASH = "1fce392f92a1"` and implement an independent Python
oracle only for generator tests and semantic probes.

**Reason.** Rule smoke and authority synchronization already showed that the
selected transformation was correct. The defects were in input generation,
validation, and lesson identifiability, so changing authority would add risk
without addressing the root cause.

**Rejected alternative.** Rewrite or generalize the Racket rule. Rejected
because no counterexample showed an authority error and the canonical outputs
already matched the intended divider reflection.

## D2: Replace rather than simulate the old override surface

**Decision.** Remove the nine-axis imported interface and expose five exact,
observable controls: `profile_kind`, `divider_side`, `source_scale`,
`source_palette`, and `layout_kind`.

**Reason.** The old axes mixed ignored metadata, singleton labels, dimensions
that were silently normalized, and invalid “degenerate” scenes. An exact
control should be recoverable from the returned grid and should either be
honoured or explicitly rejected. `observe_overrides()` now makes that contract
executable.

**Rejected alternatives.** (1) Keep all old axis names and invent weak aliases;
this would preserve misleading semantics. (2) Mark ignored controls advisory;
this would still let callers believe they controlled the distribution. (3)
Continue accepting unknown keys; this hides typos and provenance errors.

**Probe.** The final override gate exercised 131 cases over 11,790 draws with no
findings and rejected an unknown key. See
`checks/after-complete/checks/9baf979683ef_after_override_results.json`.

## D3: Retain canonical morphology while broadening structure

**Decision.** Sample the three canonical shapes (`7x11`, `8x9`, `7x13`) with
high weight and add `9x12` and `10x15`. Vary one to four source colours and
connected, scattered, or mixed source topology.

**Reason.** The repair needs more than random coordinates, but should not drift
so far from canonical examples that the generated task becomes a different
visual distribution. Expanded profiles add width/height variation while the
canonical profiles remain common in every band.

**Rejected alternatives.** (1) Arbitrary `5..14` dimensions: wider coverage but
less controlled profile support and more capacity edge cases. (2) Only the
three canonical profiles: safer but unnecessarily narrow. (3) Fixed two-colour
sources: close to canonical palette size but leaves colour-cardinality
shortcuts untested.

**Measured outcome.** The profile gate found 26 exact canonical profile hits in
60 draws, with at least six in every band. The 100-draw task-local samples found
54 easy, 52 medium, and 34 hard canonical-profile inputs.

## D4: Make each production scene refute the two canonical shortcuts

**Decision.** Put the divider exactly one column left or right of the midpoint
and generate six to eight source cells. Declare the midpoint mirror and
first-five-only programs as canonical shortcuts, semantic rivals, and lesson
competitors.

**Reason.** Both rivals fit all 3/3 canonical examples. Merely hoping that a
multi-example lesson contains a counterexample is weaker than making every
sample informative, and it makes the failure mode easy to test.

**Rejected alternatives.** (1) Mix centred/off-centre and five/more-than-five
scenes uniformly: more natural-looking, but some short lessons would remain
shortcut-compatible. (2) Depend only on `lesson_identifiable()` rejection:
correct but wastes generated candidates and makes teaching quality sensitive
to assembly policy. (3) Add unrelated transformations such as horizontal
mirrors: outside the authority and therefore invalid.

**Failure mode introduced.** The generated distribution overweights
counterexamples and underrepresents two valid canonical conditions. This is
intentional teaching pressure, not a domain restriction; canonical inputs are
still accepted by validation and the oracle. Future data mixtures may add
centred/five-source evaluation-only cases after shortcut-resistant lessons are
secured.

## D5: Use directly checkable topology classes

**Decision.** Define connected, scattered, and mixed layouts by 4-neighbour
components, with deterministic templates or constrained sampling.

**Reason.** These classes are recoverable from the grid, give useful structural
variation, and avoid ambiguous metadata-only labels. Every layout spans at
least two reflection distances so a single-column-copy heuristic is not enough.

**Rejected alternative.** A continuous density axis. With only six to eight
sources and several grid profiles, density would be a coarse derived label and
would overlap heavily with source count and shape.

## D6: Validate lessons, not only individual examples

**Decision.** Add `lesson_identifiable()` and a task-local cyclic audit that
rotates every member of a deterministic four-pair window into query position.
The tool imports the generator’s own rival declarations instead of maintaining
an independent name list.

**Reason.** Witness frequency in individual samples does not prove that every
assembled lesson teaches the intended distinction. The shared census checks
production lessons but explicitly does not rotate all query positions; the
local tool closes that gap for this task.

**Measured outcome.** The shared census materialized 300/300 lessons with zero
declared ambiguity. The local tool tested 1,200 cyclic rotations with zero
ambiguous rotations and no surviving declared rival.

**Limit.** This remains a finite declared-rival test. It does not prove universal
identifiability or measure semantic distance between unique grids.

## D7: Build reusable regression and audit artifacts

**Decision.** Add nine focused tests under the selected task and retain
`workspace/audit_distribution.py`.

**Reason.** The tests cover canonical parity, exact override recovery, shortcut
fit/refutation, lesson windows, semantic witnesses, deterministic generation,
mutation rejection, and the reusable audit tool itself. The workspace tool
lets later reviewers add rival functions to the generator and rerun the same
source-bound distribution/cyclic analysis.

**Result.** The selected portable task-test stage passes 9/9.

## 2026-10-24 native parametric receiver-action extension

The canonical default remains the exact selected Racket source. The new
`receiver_action=absorb_color` setting composes canonical reflection (A) with an
input-dependent receiver absorption (B): only the reflected intermediate
creates a source-color contact with one color-9 component, and B consumes that
contact to choose both the component and recolor value.

The first sampler draft could exhaust every legal receiver location after a
dense mirror field was drawn. Receiver geometry is now reserved before the
remaining source field. A wider seed sweep then found that greedy decoy
placement could consume the only footprint for a later receiver; bounded joint
backtracking replaced the greedy draw. The protected causal audit exposed a
separate witness-only defect: the Python counterfactual helper inspected
*predicted* mirror coordinates and treated an absent mirror as a zero-color
contact. It now inspects actual source-colored cells in the supplied
intermediate, matching the standalone Racket B program.

Retained source-bound evidence:

- `workspace/parametric/evidence/current/summary.json`: 64 seeds, 128 episodes,
  1,280 labeled pairs, 640 teaching checks, zero failures.
- `workspace/parametric/evidence/current/protected-racket.json`: 40 label
  evaluations plus four A/B counterfactual evaluations, zero mismatches.
- `workspace/parametric/evidence/current/causal-witness.json`: exact programs,
  input, intermediate, lawful output, skip-A output, and wrong-intermediate
  output.
- `workspace/parametric/evidence/manifest.json`: current source/evidence
  inventory; reviewer-reported only.
- `checks/9baf979683ef/qualification/qualification.json` and sibling
  `execution.json`: native qualification for two settings × seeds 0/17,
  40 protected-Racket evaluations, status `qualified`.

This finite family is reviewer-ready and owner-pending. It is not accepted,
training-admitted, or a proof against arbitrary alternative programs.
