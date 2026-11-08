# Working notes: 6b4b56166bfd

## Current design (v2.0.0)

**Intended rule.** A lawful input has one color-5 pivot at `(height//2,
width//2)` and one to three distinctly colored seed cells.  The selected Racket
rule copies every seed through its complete four-position 90-degree rotation
orbit around that pivot.  Racket remains the output authority; this repair did
not change canonical data or rule source.  The canonical rule hash is pinned as
`f2aaf100dc45`.

**Lawful domain.** Grids are 5..14 by 5..14.  Seeds use distinct colors from
`{1,2,3,4,6,7,8,9}`, have nondegenerate in-bounds orbits, and no two seeds share
an orbit.  The only public exact controls are `grid_h`, `grid_w`, and
`n_cells`; they are independently observable from a returned grid.  Unknown
controls, booleans, fractional/string controls, negative sample indices, and
non-ARC cell values fail closed.

**Sampling.** Three quarters of ordinary draws are anchored to a canonical
profile `(7,7,2)`, `(9,9,2)`, or `(9,9,3)`; the remaining draws, plus lower
weight in every anchored draw, retain support over the full declared 5..14 and
1..3 domains.  Difficulty changes weights, not legality.  Candidate orbits are
enumerated over the whole grid rather than a radius-2 neighborhood, so the
canonical radius-3 cases are reachable.

## Reversed decisions and evidence

The selected baseline (`cc00e3bc87d2500593dc14319e5f06ec11273bfa4c1912415b7691153ea70228`)
advertised nine controls while only grid size and seed count affected pixels;
it sampled dimensions only in 6..8, silently accepted unknown/fractional
controls, and allowed invalid ARC cell values through `self_check`.  It also
restricted seed candidates to radius 2.  Those choices were replaced by the
three-axis exact contract above.  The prior review index was used as a lead,
then each defect was reproduced by a failing test before implementation; the
compact reproducer is
`counterexamples/review-921182f345e32906/contract_regressions.json`.

Final source hash:
`f5199baa50a2c21157599f14b282471082818630273d028e420116e61353e84b`.
The final after battery is 12/12 green.  Its 60-draw profile gate accepted all
five canonical inputs and found exact canonical profiles in easy 11/20,
medium 11/20, and hard 7/20.  The exact override matrix completed 16,740 draws
with zero findings.  A 300-lesson census (three demonstrations plus one query)
reported no ambiguity in 1,200 production-query and 1,200 rotated-query checks
against the declared half-turn rival.

## Known limits

The semantic claim is finite: it refutes the declared `half_turn_only` rival
and the gate's bounded generic mutations, not every conceivable program.  The
random 300-lesson census is broad but does not enumerate every seed or every
possible curriculum schedule.  Training approval remains external; this review
only establishes generator and lesson-check behavior for the measured source.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-253fc9afa0fa70eb:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `f5199baa50a2c21157599f14b282471082818630273d028e420116e61353e84b`. At disposition, audited bytes match the current source.

### Current decision

Source prose means `repo/generators/6b4b56166bfd/generator.py`. Reviewer-reported on unchanged source f5199baa50a2c21157599f14b282471082818630273d028e420116e61353e84b. No issue in bounded inspection on unchanged audited source: strict defect lint passes and33 portable tests reported passed, covering5 canonical pairs, exact controls/rejections,480 generated orbit draws, radius3, profile floors and half-turn rival. No universal approval or unmeasured claim. Quoted basenames mean these exact target-local paths: `checks/audit/6b4b56166bfd/defect-command.exit` `checks/audit/6b4b56166bfd/defect-command.log` `checks/audit/6b4b56166bfd/defect/RUNTIME_MANIFEST.json` `checks/audit/6b4b56166bfd/defect/checks/6b4b56166bfd_audit_battery_summary.json` `checks/audit/6b4b56166bfd/defect/checks/6b4b56166bfd_audit_commands.jsonl` `checks/audit/6b4b56166bfd/defect/checks/6b4b56166bfd_audit_defect_lint.log` `checks/audit/6b4b56166bfd/defect/checks/6b4b56166bfd_audit_defect_lint.ok` `checks/audit/6b4b56166bfd/defect/checks/6b4b56166bfd_audit_defect_lint.receipt` `checks/audit/6b4b56166bfd/defect/progress.log` `checks/audit/6b4b56166bfd/defect/result.json` `checks/audit/6b4b56166bfd/task-tests-command.exit` `checks/audit/6b4b56166bfd/task-tests-command.log` `checks/audit/6b4b56166bfd/task-tests/RUNTIME_MANIFEST.json` `checks/audit/6b4b56166bfd/task-tests/checks/task_tests.xml` `checks/audit/6b4b56166bfd/task-tests/progress.log` `checks/audit/6b4b56166bfd/task-tests/result.json`

### Assessment or prior finding

## 6b4b56166bfd

**No issue found in the bounded inspection; target left unchanged.** The drawn
source is SHA-256
`f5199baa50a2c21157599f14b282471082818630273d028e420116e61353e84b`.
Strict audit defect lint passed, and the portable task-test stage passed 33/33
with zero failures/errors/skips. Those tests cover the canonical rule hash and
five canonical pairs, exact override observability across bands, invalid call
and override rejection, malformed-cell handling, 480 generated draws with
disjoint in-bounds quarter-turn orbits, radius-three support, per-band profile
floor, and a half-turn-only rival witness. Evidence:
`checks/audit/6b4b56166bfd/defect/result.json` and
`checks/audit/6b4b56166bfd/task-tests/result.json`. This is not an approval or a
claim beyond those checks.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `f5199baa50a2c21157599f14b282471082818630273d028e420116e61353e84b`.

# Decisions for 6b4b56166bfd

## D1 — Replace the advertised nine-axis surface with three exact controls

**Prior choice.** The baseline advertised dimensions, palette descriptors,
counts, density, position bias, and texture even though several were singleton,
dead, aliases, or silently ignored.

**Decision.** Keep only `grid_h`, `grid_w`, and `n_cells`, because each is a
meaningful input choice and can be recovered exactly from the returned grid.
Unknown names and non-integral/out-of-range values fail closed.

**Why.** An inert control produces mislabeled experimental metadata and lets a
typo look successful.  The baseline override probe produced thousands of such
findings; the final matrix executed 16,740 draws with zero findings
(`checks/after/checks/6b4b56166bfd_after_override_results.json`).

**Rejected alternative.** Retaining texture/palette axes and inventing cosmetic
color families would add complexity without teaching a new relation.  Seed
colors already vary across all legal non-{0,5} ARC colors.

## D2 — Preserve full domain support while strongly anchoring canonical profiles

**Decision.** Public dimensions remain 5..14 and seed count 1..3.  Ordinary
sampling chooses a canonical profile 75% of the time and keeps lower-weight
support for every declared value; difficulty changes weights but not legality.

**Why.** The old 6..8-only sampler contradicted its 5..14 metadata and missed
two canonical sizes.  Purely canonical-only sampling would fix coverage at the
cost of useful extrapolation.  The weighted mixture yields exact profile hits
in every band—easy 11/20, medium 11/20, hard 7/20—while retaining broad shapes
(`checks/after/checks/6b4b56166bfd_after_profile_floor.json`).

**Rejected alternatives.** (1) Narrowing the public domain to 7×7/9×9 would be
honest but unnecessarily discard rectangular and larger lawful cases.  (2)
Uniform 5..14 sampling made canonical support unnecessarily sparse.  (3)
Difficulty-specific legality would make exact overrides inconsistent across
bands.

## D3 — Enumerate complete rotation orbits over the whole grid

**Decision.** Build all nondegenerate, fully in-bounds four-position orbits and
sample distinct orbits directly.

**Why.** The baseline already avoided two seeds in the same orbit, but it only
searched a radius-2 neighborhood.  Canonical 9×9 inputs include radius-3 cases.
The new enumerator makes every legal orbit available and makes disjointness
structural rather than probabilistic.  Focused tests exercise 480 ordinary
draws and a pinned radius-3 census.

**Failure mode checked.** Even or rectangular dimensions can have asymmetric
available area around the floor-center pivot; the implementation admits only
orbits whose four members are in bounds.  Every declared 5..14 shape has more
than enough candidates for three seeds.

## D4 — Make validation a real domain predicate

**Decision.** `self_check` now validates shape, ARC integer cell values (rejecting
`bool`), dimensions, central unique pivot, seed count, distinct colors,
complete orbits, and disjointness.  Call scalars and overrides are validated
before constructing the generation context.

**Why.** The old validator accepted `True`, `2.75`, strings, and out-of-range
colors.  These are data-integrity failures, not benign coercions.  The retained
counterexample record is
`repo/generators/6b4b56166bfd/counterexamples/review-921182f345e32906/contract_regressions.json`.

## D5 — Add an executable semantic contract without changing authority

**Decision.** Add a pure-Python mirror for tests, a plausible
`half_turn_only` rival, a quarter-turn witness, shortcut declarations, and
`lesson_identifiable`.  Keep the selected Racket source unchanged and pin its
hash `f2aaf100dc45`.

**Why.** Correct individual labels do not prove that a three-demonstration
lesson distinguishes the intended fourfold rule.  The declared rival is simple,
canonical-plausible, and differs on every lawful generated seed.  The smoke gate
found 12/12 identifiable lessons and 48/48 unambiguous query rotations.  The
larger required-rotation census found zero ambiguity among 300 lessons, 1,200
production queries, and 1,200 rotated queries
(`checks/lesson-census-final.json`).

**Limit.** This is finite rival testing.  It does not prove uniqueness against
all programs or all possible curriculum schedules.

## D6 — Testing and retained failures

Tests were written first and observed failing: 28 failed and 5 passed against
the baseline-facing implementation.  After the repair, all 33 pass.  The
baseline aggregate battery was interrupted by the command-window cap, so its
measured evidence is reported as partial rather than promoted to a complete
verdict; focused baseline logs retain the lint, defect, profile, semantic, and
override failures.  The unchanged final source completed the resumable after
battery at 12/12 green with no interrupted stages.
