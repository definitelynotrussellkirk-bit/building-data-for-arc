# Working notes: 611cc0f4e0fe

## Selected repair (2026-10-04)

- Baseline generator SHA-256:
  `b411e57b888a97e2a969e5a14432c3891aba04e2e87d5f41c72a1b8f1095ab61`.
- Selected generator SHA-256:
  `d4ec1012858b37a8c0c2de83844cb4731062f979246cdb53b379fbdf8c099af1`.
- Canonical authority hash: `51d7c63afd4f`; authority source was not edited.
- No prior return was used as a lead; diagnosis started from this packet's
  immutable baseline and before-battery evidence.

The baseline exposed many axes it did not honor, lacked `RULE_HASH`, accepted
any non-axis-aligned pair as “diagonal,” and generated only valid 45-degree
pairs. The selected repair replaces the fictional control surface with one
observable semantic profile and schedules four profiles that explicitly refute
canonical-fitting shortcuts.

The task-local auditor is `workspace/audit_curriculum.py`; regression tests are
under `tests/`. Root-level `REVIEW.md` and `DECISIONS.md` contain the measured
before/after evidence and full rationale.

## Known domain limits

The generator uses exactly two cells per nonzero color, fixed canonical-sized
dimensions per difficulty band, no axis-aligned decoy, and nonintersecting paths
except the canonical-compatible endpoint-crossing allowance. These are finite
curriculum choices, not a proof that no undeclared rival exists.
## Current reviewer considerations

Source SHA-256: `d4ec1012858b37a8c0c2de83844cb4731062f979246cdb53b379fbdf8c099af1`.

# Decisions — `611cc0f4e0fe`

## D1 — Preserve the selected Racket authority

**Decision.** Leave `repo/shared/data/canonical/puzzles.jsonl` and the retained
base solution untouched; pin `RULE_HASH = "51d7c63afd4f"` in the generator.

**Rationale.** The rule itself is coherent: for each nonzero color, it takes the
first and last row-major cells and fills only when their displacement is an exact
45-degree diagonal. Baseline rule smoke and authority sync were already green;
the defects were in generation, validation, and teaching support.

**Alternatives rejected.** Broadening the Racket rule to generic lines would make
the canonical-fitting shortcut authoritative rather than fix the curriculum.
Changing the rule to require exactly two cells per color would unnecessarily
narrow a correct existing authority.

**Probe.** Final battery `rule_smoke`, `racket_lint`, and `authority_sync` are green;
`checks/question/611cc0f4e0fe/racket.json` executes the pinned rule on a separating
witness.

**Limitation.** Generation does not currently exercise the authority's behavior
for colors occurring more than twice.

## D2 — Replace the advertised axis surface instead of implementing dead controls

**Decision.** Remove the baseline's nine mostly fictional axes and expose only
`scene_profile` with four exact values. Reject every unknown override.

**Original rationale.** Unknown. The imported notes were empty. The baseline source
claimed grid size, palette, pair count, density, position, and texture controls, but
its implementation read only a subset and aliased or ignored the rest.

**Alternatives considered.** Implementing every legacy axis would expand the state
space without adding semantic information and would make exact observability much
harder. Removing all controls would pass less information to audit tooling and make
adversarial profiles difficult to force.

**Probe.** `observe_overrides` identifies each profile from the grid; forced profile
tests cover all bands; final `override` stage is green. Unknown and invalid values
have direct regression tests.

**Failure mode / limitation.** One semantic axis intentionally sacrifices arbitrary
size, palette, and density control. The chosen axis is fully truthful rather than
nominally broad.

## D3 — Use a four-profile semantic curriculum

**Decision.** Schedule the following period-four sequence:
`canonical_opposite_slopes`, `same_slope_pairs`, `off_slope_decoy`, `three_pairs`.
`EXAMPLES_NEEDED = 4` matches one complete cycle.

**Rationale.** The profiles each carry one specific teaching obligation while
preserving a simple grammar:

- canonical support;
- same-slope validity;
- exact-45° discrimination from a generic line;
- more than two colors and more than one transformed pair.

Together they refute every declared competitor in each four-demo lesson.

**Alternatives rejected.** Pure random mixing could leave a lesson without its
critical counterexample, as reproduced in audit target `d3ae93aa8d37`. A larger
profile set would require more demonstrations and dilute the smallest complete
lesson. Axis-aligned decoys alone would not refute a shortcut that connects every
non-axis repeated pair.

**Probes.** `test_one_scheduled_lesson_refutes_every_declared_rival`, production
census `300/300`, and the cyclic task-local auditor `12/12`.

**Failure mode / limitation.** The deterministic order is itself observable only
through sample sequencing, not through a marker in the grid. The cyclic audit covers
every query position, but arbitrary nonconsecutive lesson assembly is not promised.

## D4 — Keep dimensions canonical-sized and band-specific

**Decision.** Use `7×7` for easy, `8×10` for medium, and `10×10` for hard.

**Rationale.** All are present in the canonical dimension set, satisfy the inherited
profile floor, and are large enough to place the required disjoint paths. Fixed
dimensions make the semantic observer exact and isolate geometric difficulty from
irrelevant shape variation.

**Alternatives considered.** Random dimensions within broad ranges would increase
surface diversity but could make profile recognition ambiguous and had contributed
to baseline hard-band strict-profile failure. A single dimension for all bands would
remove even modest scale variation.

**Probe.** Final `profile_floor`, `strict_canonical_like`, and all-band forced audit.

**Failure mode / limitation.** Grid size can correlate with difficulty; it is not a
causal rule feature. This is documented rather than hidden behind a dead override.

## D5 — Use canonical foreground colors but randomize assignments

**Decision.** Draw distinct colors from `(2, 3, 4, 5, 6, 7, 8)` and always retain
background `0`.

**Rationale.** The rule is color-agnostic, while this set stays inside colors already
seen in the canonical task and supplies enough distinct values for three pairs.
Random assignment prevents a fixed color from carrying a profile role.

**Alternatives rejected.** All ARC colors would add no semantic coverage and could
make palette-based strict matching less stable. Fixed profile-specific colors would
create an avoidable shortcut.

**Probe.** Determinism tests, profile observer tests, diversity stage, and 1,499
unique production inputs among 1,500 lesson pairs.

**Failure mode / limitation.** Colors `1` and `9` are not generated; color identity
invariance is inferred from varied assignments, not exhaustively enumerated.

## D6 — Constrain path geometry to make outputs unambiguous

**Decision.** Require valid diagonal lengths of at least two steps, exactly two cells
per nonzero color, no overlapping endpoints, and no interior-to-interior path
intersections. The canonical opposite-slope profile permits the canonical-compatible
case where one segment crosses at the other segment's endpoint.

**Rationale.** Every output must be nonidentity and attributable to the intended
pair. Unsafe overlaps can overwrite colors and make a correct rule appear wrong.
The minimum length guarantees at least one painted interior cell.

**Alternatives considered.** Allowing arbitrary crossings would broaden geometry but
requires an explicit overwrite-order curriculum. Length-one pairs would leave the
output unchanged and are rejected by inherited validation.

**Probe.** `analyze_grid`, `self_check`, rule-mirror equality, rule smoke, and tests
for blank, axis-aligned, shallow, and off-slope cases.

**Failure mode / limitation.** Overwrite semantics and multiple cells of one color
remain out of domain.

## D7 — Mirror the authority exactly, but validate the generated grammar strictly

**Decision.** `rule_mirror` groups cells in row-major order, uses the first and last
cells, and fills only exact 45° paths. `self_check` accepts only declared scene
profiles and rejects malformed, blank, identity, axis-aligned, or unsupported color
groups.

**Rationale.** The baseline checker used “row changes and column changes” as a proxy
for diagonal, which admitted the decisive 3-by-2 impostor. A separate exact mirror
lets tests compare intended behavior without importing private runner functions.

**Alternatives rejected.** Reusing the baseline loose predicate would preserve the
bug. Calling Racket from the generator would couple generation to the executor and
make tests slow; Racket remains the final authority in supported checks.

**Probe.** Exact non-45 witness test, authority-bound `arcpuzzles apply`, task tests,
and rule smoke.

**Failure mode / limitation.** Strict validation intentionally rejects lawful inputs
outside the teaching grammar even though the authority may execute them.

## D8 — Declare competitors, witnesses, and lesson identifiability in executable form

**Decision.** Add four `SEMANTIC_RIVALS` / `LESSON_COMPETITORS`, three
`CANONICAL_SHORTCUTS`, five witnesses, witness-to-rival mappings, and a
`lesson_identifiable` hook that requires all four profiles and refutes every rival.

**Rationale.** Natural-language counter-hypotheses are not testable. The canonical
examples alone admit three materially different rules; the contract must prove that
generated lessons separate them.

**Alternatives considered.** Relying only on witness frequency can still assemble a
bad lesson. Relying only on the hook can hide a stale copied rival list. The chosen
combination uses generator declarations as the source of truth and checks both
individual cases and complete lessons.

**Probe.** Semantic gate, shared lesson census, and task-local auditor.

**Failure mode / limitation.** This is a finite rival set. An undeclared program may
still fit all sampled lessons.

## D9 — Set `MIN_STRICT_FRAC` to a measured conservative floor of `0.20`

**Decision.** Use `0.20`, not the nominal profile share `0.25`.

**Rationale.** The pinned semantic census samples 600 `(seed, sample_index)` pairs
using its own deterministic recipe; it observed 132 canonical-profile cases, or
`22%`. A `25%` declaration failed despite complete profile support because the
census does not enumerate an exact multiple of each schedule start. The floor should
be a lower bound supported by the tool's population, not an asserted expectation.

**Alternatives rejected.** Keeping `0.25` would make the final gate flaky against its
pinned sampler. Dropping to the global `0.05` would understate intended canonical
support.

**Probe.** The failing test is retained at `checks/test_floor_red.log`; the final
semantic report records `0.22 >= 0.20` with no advisory.

**Failure mode / limitation.** This threshold is tied to the current shared sampler;
a future sampler change should rerun the census before changing it.

## D10 — Build a portable curriculum auditor rather than only prose

**Decision.** Add `workspace/audit_curriculum.py` and tests for its report/CLI.

**Rationale.** The shared production census intentionally does not rotate every pair
into the query position. The task's short deterministic schedule makes exhaustive
cyclic rotation cheap, and future edits need a repeatable check rather than a manual
claim.

**Alternatives considered.** A one-off notebook or inline script would not survive
the handoff. Patching shared tooling is outside the selected-task delta.

**Probe.** `16` seeds × `3` bands × `4` forced profiles = `192` cases, plus `12`
cyclic lessons. The tool exits nonzero on observer, validator, rival, canonical-fit,
or lesson failures.

**Failure mode / limitation.** It uses the Python mirror for bulk cases; supported
Racket battery/census remains required for authority binding.

## D11 — Preserve all material failed iterations

**Decision.** Retain the baseline failed battery and the test-first failures for the
initial repair, curriculum auditor, and strict-floor correction.

**Rationale.** They demonstrate that tests exercised missing behavior rather than
merely confirming the final implementation.

**Evidence.** `checks/before/`, `checks/test_red.log`,
`checks/test_audit_red.log`, and `checks/test_floor_red.log`.

## Remaining limitations

The selected generator is intentionally an endpoint-pair curriculum. It does not
cover colors appearing three or more times, axis-aligned decoys, arbitrary path
overlap/overwrite order, every ARC color, or every grid dimension accepted by the
Racket rule. The 300-lesson census and declared-rival probes give strong measured
support for this domain, not a universal induction proof.
