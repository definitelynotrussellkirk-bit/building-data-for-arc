# Working notes: e438ce3e02ce

## Review 2026-10-03 — assignment review-10a1b6666e3f2f75

No prior return was used as implementation authority or as current-source
evidence. The retained associated notes were effectively empty; the only lead
was the baseline source comment saying fixed three-seed positions had recently
been replaced by random 3–5 seed layouts. All findings below were reproduced
against the packet's pinned baseline.

Baseline generator SHA-256:
`b530ca04903d8cf1835873369f70452a3103db9f49bc405fe04276db8199b410`.
The first battery reached five stages before the controller execution was
interrupted. It reproduced missing `RULE_HASH`, stale/dead axes and textures,
8,415 override findings, only 5/60 canonical-envelope profile hits (0/20 hard),
and no semantic contract. The retained partial evidence is under
`checks/before*`.

The repair replaces the stale nine-axis surface with exact observable
`grid_h`, `grid_w`, and `n_seeds` controls, pins canonical rule hash
`866bf2f14b22`, and installs an eight-slot linked curriculum. Every cyclic
four-example window contains 3-, 4-, and 5-seed cases, a 3-way tie, a
Manhattan/Euclidean equivalent control, metric discriminators at all seed
counts, and consequential fourth/fifth seeds. Canonical strict support is the
four 3-seed slots (about 50%).

Task-local tests were written first and observed failing (9 failed, 1 passed).
After the first implementation they passed 10/10. The integrated defect lint
then found byte-identical difficulty bands; a new regression observed 0/96
band-diverse cases before the fix. Salting only the layout RNG by band moved the
suite to 11/11 and the standalone defect lint to green.

Final generator SHA-256:
`60a2cee1c491a112a7d37e67336131257da46cdb417cc03b92fc6c176a068c7f`.
The completed final battery is 12/12 green, portable task tests are 11/11 green,
and the 300-lesson Racket-backed census has zero declared-rival survivors.
The selected Racket rule was not changed.
## Current reviewer considerations

Source SHA-256: `60a2cee1c491a112a7d37e67336131257da46cdb417cc03b92fc6c176a068c7f`.

# Distribution decisions: e438ce3e02ce

Finding cross-reference: **G1** exact contract cleanup; **G2** semantic curriculum and canonical support; **G3** band-diversity regression; **G4** independent probe. Required shortcut evidence is **Q1**; adversarial audits are **A1** and **A2** in `AUDIT.md`.

## Scope and authority

**Choice.** Keep the canonical Racket rule unchanged and pin
`RULE_HASH = "866bf2f14b22"`; repair only the Python generator, tests, summary,
and task workspace.

**Rationale.** The rule exactly matches all five canonical pairs and the final
Racket rule-smoke/authority stages are green. The observed failures were in the
input contract and lesson distribution, not the authority.

**Rejected alternative.** Rewriting the Racket rule would widen risk without
addressing stale axes, low canonical support, or ambiguous lessons.

**Prior evidence.** No prior return was used as current evidence. The associated
notes contained no substantive repair proposal. The baseline source comment
about a prior fixed-position defect was treated only as a lead and remeasured.

## Input grammar and exact controls

**Choice.** Inputs are rectangular 9–10 by 9–12 grids with zero background and
exactly 3–5 singleton seeds in pairwise-distinct colors excluding 0 and 8. The
only public axes are `grid_h`, `grid_w`, and `n_seeds`; every one is recovered by
`observe_overrides` and every legal joint combination is constructive.

**Rationale.** These dimensions are the canonical envelope. Seed count is the
semantic extension needed to refute “ignore later seeds.” Distinct seed colors
make tie output unambiguous and match all canonical inputs.

**Rejected alternatives.** The baseline's `palette_kind`, `anchor_corner`,
`asymmetry_force`, `palette_size`, `position_bias`, `n_distinct_colors`, and
`texture` controls were removed because they were singleton, ignored,
byte-identical, or actively outside the normal domain. Degenerate textures were
removed rather than pretending malformed examples were normal exact controls.
The old 8..12 size range was rejected because it drove canonical-profile support
to 5/60 overall and 0/20 hard.

**Failure modes and limits.** The grammar does not claim behavior for duplicate
seed colors, color-8 seeds, more than five seeds, or sizes outside the canonical
envelope. Those are rejected rather than silently interpreted.

## Seed-layout construction

**Choice.** Every normal or overridden layout must contain at least one blank
tie, at least one uniquely-owned blank, and at least one uniquely-owned blank
for every seed. Random layouts also reject adjacent seed collisions and use a
bounded deterministic search.

**Rationale.** A seed that owns no blank region is decorative and cannot refute
an ignore-extra-seed shortcut. A layout with no tie fails to teach the cyan-8
branch. A layout with no unique cells fails to teach color propagation.

**Rejected alternatives.** Unconstrained random positions were fast but could
produce decorative seeds and relied on chance for semantic distinctions. Fixed
canonical-like triangles made the geometry itself a shortcut. Rejection at
lesson assembly was rejected because the invariant belongs in the generator and
must replay from `(seed, sample_index, band)`.

**Probe.** `workspace/voronoi_probe.py` independently reports seed ownership,
tie arity, metric disagreement, and first-three/first-four shortcut
disagreements without importing generator helpers.

## Four-example teaching schedule

**Choice.** Use eight slots repeating roles A/B/C/D twice:

1. A — 3 seeds, a genuine 3-way Manhattan tie, and metric disagreement.
2. B — 4 seeds, metric disagreement, consequential fourth seed.
3. C — 3 collinear seeds with identical Manhattan/Euclidean output labels.
4. D — 5 seeds, metric disagreement, consequential fifth seed.

The second A/B/C/D cycle uses different canonical profiles. Every cyclic window
of four includes all roles and 3/4/5 seed counts.

**Rationale.** Canonical pairs contain only three seeds, so “ignore all seeds
after the first three” and “ignore all seeds after the first four” both fit all
five public pairs. The schedule deterministically refutes both, while also
separating Manhattan from Euclidean distance and showing that a 3-way tie uses
the same color-8 marker.

**Rejected alternatives.** Independent random role draws permit complete
ambiguous lessons. Four slots alone would cover the semantics but only two
canonical size profiles; eight slots provide all four canonical profiles while
preserving the four-example guarantee. Making every example a discriminator was
rejected because the metric-equivalent control is useful evidence that geometry,
not a memorized diagonal pattern, determines equivalence.

**Measured result.** Task tests exhaust every cyclic start in every band. The
production census materialized 300 lessons (100 per band, four demos plus one
query), 1,498 unique inputs, and zero declared-rival survivors.

## Canonical support

**Choice.** Four of eight slots are exact canonical profiles:
`(9,9,3)`, `(10,10,3)`, `(9,11,3)`, and `(10,12,3)`. Declare
`MIN_STRICT_FRAC = 0.45`.

**Rationale.** This keeps roughly half the curriculum close to public examples
while reserving half for 4/5-seed shortcut counterexamples.

**Measured result.** The semantic gate measured 308/600 strict draws (51.33%):
101/200 easy, 103/200 medium, and 104/200 hard. Profile floor hit an exact
canonical size/palette profile 9/20 easy, 10/20 medium, and 11/20 hard; all five
canonical inputs were accepted.

## Difficulty bands

**Choice.** Preserve the same semantic schedule and exact axis profiles in all
bands, but use a band-keyed layout RNG and require at least 1/2/3 metric-label
disagreements for easy/medium/hard discriminator roles.

**Rationale.** A difficulty change should not remove required lesson branches or
change exact override meaning. It should still produce materially different
instances and modestly strengthen the discriminator.

**Rejected alternative and failure.** The first implementation changed only the
acceptance threshold. Because the same deterministic candidate passed all
thresholds, defect lint found all sampled bands byte-identical. A regression
captured 0/96 diverse cases before the band-keyed layout salt; the final test
requires at least 90% of sampled cases to differ and passes.

**Limit.** Difficulty is not a formal human-solvability ordering. It controls
layout realization and discriminator margin, not grid size or rule complexity.

## Executable semantic contract

**Choice.** Provide a Python mirror, strict validator, semantic witnesses,
canonical shortcuts, lesson competitors, and a four-demo
`lesson_identifiable` hook. Declared rivals cover Euclidean distance globally
and conditionally at each seed count, ignoring seeds after three/four, leaving
ties blank, and mishandling three-way ties.

**Rationale.** Frequency-only metadata cannot prove that generated examples
actually distinguish a rule. Each witness is tied to an executable rival, and
the lesson hook checks exact outputs plus competitor refutation.

**Measured result.** The semantic gate checked 600 draws with no crashes or hook
errors; all seven witnesses fired in every band and all 60/60 sampled witness
claims held. Its 12 Racket-backed smoke lessons were 12/12 identifiable. The
deeper census was 300/300 unambiguous.

**Limit.** These are finite, declared rivals. Passing them does not prove unique
induction among all programs. The shared census used period 6 rather than the
8-slot schedule; task-local tests separately cover all eight cyclic starts.

## Self-review for new shortcuts

The new schedule could itself leak role from `sample_index mod 8`, but solvers
see grids, not sample indices, and each role has randomized positions and
colors. More importantly, a role-specific solver cannot answer all four demos
and the next query unless it still recovers nearest-seed semantics; every cyclic
window mixes all roles and the tests rotate every start.

The restriction to distinct seed colors and 3–5 seeds remains deliberate. It
makes seed identity observable and focuses the lesson on distance/ties; it does
not establish behavior for duplicate-colored seeds or unbounded seed counts.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-2f4f897fe5f87c8d:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `60a2cee1c491a112a7d37e67336131257da46cdb417cc03b92fc6c176a068c7f`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/e438ce3e02ce/generator.py, unchanged SHA256 60a2cee1c491a112a7d37e67336131257da46cdb417cc03b92fc6c176a068c7f. Ordered-policy condition, not a reproduced production defect:11 tests,308/600 strict above0.45 floor,12 ordered four-demo lessons pass;27/60 diagnostic rotations ambiguous with exact accepted witness and independent Racket replay.5760 deterministic draws/5737 unique no generation failure. Preserve fixed order; arbitrary rotation not qualified and would require redundant3/4/5-seed witnesses. Exact report/source retained in generators/e438ce3e02ce/evidence/bounded-audit-2f4f897fe5f87c8d/manifest.json. Quoted basenames mean these exact target-local paths: `checks/audit/e438ce3e02ce-combined-command.exit` `checks/audit/e438ce3e02ce-combined-command.log` `checks/audit/e438ce3e02ce-combined/RUNTIME_MANIFEST.json` `checks/audit/e438ce3e02ce-combined/checks/e438ce3e02ce_audit_battery_summary.json` `checks/audit/e438ce3e02ce-combined/checks/e438ce3e02ce_audit_commands.jsonl` `checks/audit/e438ce3e02ce-combined/checks/e438ce3e02ce_audit_semantic_gate.json` `checks/audit/e438ce3e02ce-combined/checks/e438ce3e02ce_audit_semantic_gate.log` `checks/audit/e438ce3e02ce-combined/checks/e438ce3e02ce_audit_semantic_gate.ok` `checks/audit/e438ce3e02ce-combined/checks/e438ce3e02ce_audit_semantic_gate.receipt` `checks/audit/e438ce3e02ce-combined/checks/e438ce3e02ce_audit_summary.json` `checks/audit/e438ce3e02ce-combined/checks/task_tests.xml` `checks/audit/e438ce3e02ce-combined/progress.log` `checks/audit/e438ce3e02ce-combined/result.json` `checks/audit/e438ce3e02ce/apply-command.exit` `checks/audit/e438ce3e02ce/apply-command.log` `checks/audit/e438ce3e02ce/counterexample.json` `checks/audit/e438ce3e02ce/expected-from-census.json` `checks/audit/e438ce3e02ce/input.json` `checks/audit/e438ce3e02ce/lesson.json` `checks/audit/e438ce3e02ce/racket.json` `checks/audit/e438ce3e02ce/rival.json`

### Assessment or prior finding

## e438ce3e02ce

**Conclusion: Domain question / order-sensitive shortcut, not a reproduced production defect.** Source SHA-256: `60a2cee1c491a112a7d37e67336131257da46cdb417cc03b92fc6c176a068c7f`.

The documented fixed lesson order works: all 12 sampled four-demonstration/one-query lessons are identifiable against the declared Euclidean rivals. However, arbitrary query reassignment does not. The semantic audit checked 60 held-out positions and found 27 ambiguous rotations, each with a hook warning and no execution/scoring error. Only 33/60 rotations remain identifiable.

The first exact witness is retained under `checks/audit/e438ce3e02ce/`:

- recipe: difficulty `easy`, seed `120682136684435`, sample index `0`;
- held-out flattened pair/query index: `1`;
- demonstrations retained: indices `[0, 2, 3, 4]`;
- surviving rival: `euclidean_only_for_four_seeds`;
- `input.json`: the held-out lawful query input;
- `expected-from-census.json`: authoritative output recorded by the semantic census;
- `rival.json`: the surviving rival's different output;
- `racket.json`: independent supported `arcpuzzles apply` replay;
- `counterexample.json`: source/rule hashes, recipe, validation, counts, and command.

The query passes the target validator and belongs to the documented generator domain. Independent Racket application matches `expected-from-census.json` and disagrees with `rival.json`. The ambiguity arises because the held-out pair is the only four-seed Manhattan-versus-Euclidean discriminator in that lesson; the remaining demonstrations do not refute a rival that switches to Euclidean distance only for four seeds.

Measured context:

- 11/11 portable tests passed.
- 308/600 generated draws passed the strict-canonical profile, above the declared `0.45` floor; no crashes or hook errors were observed.
- 12/12 ordered lessons were identifiable.
- 27/60 diagnostic rotations were ambiguous; zero rotation scoring errors.
- The additional deterministic sweep covered 5,760 draws and 5,737 unique normalized inputs with no exception, nondeterminism, or `self_check` failure.

**Recommendation.** Keep the current fixed order if that is the real export contract. Before a downstream data pipeline shuffles demonstrations or rotates which pair is the query, either require rotation identifiability or construct each lesson with redundant 3-, 4-, and 5-seed Manhattan-versus-Euclidean discriminators. Unconditionally calling this a generator defect would be a false positive under the fixed-order contract, so I made no audit-target edit.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## Parametric review 2026-10-25

**Decision.** Preserve the approved Manhattan generator byte-for-byte and add a matched-input Chebyshev branch. Both settings expose the same sparse seed layouts; Step A computes the metric-dependent nearest-seed color set for every cell, and Step B maps singleton sets to their color and multi-seed sets to tie color 8.

**Evidence and reversal.** Fresh task tests, a bounded four-seed audit, protected native qualification, causal replay, and single-query privacy projection are retained under `workspace/parametric/evidence/` and `WORK/checks/e438ce3e02ce/`. The packet authoring-preflight helper was also tried, but it crashes because this approved task stores canonical `test` as one object and the helper iterates it as a list. That helper failure is retained; the exact unchanged approved source instead uses the successful native qualification receipt.

**Limit.** The fixed layouts prove the two declared metrics are distinguishable, including a 30×30 case, but do not claim universal metric identifiability or measured training gain. The next useful action is owner integration followed by fresh native qualification and acceptance on the integrated bytes.

