# ab8cb362ef4d generator notes

Version 2.0.0 replaces the narrow perfect-frame sampler. The selected Racket
authority is unchanged and pinned by `RULE_HASH = 94102b577ef7`.

The canonical examples show that a frame is the bounding box of a connected
color-5 component, not necessarily a pristine all-5 border: a non-5 marker may
overwrite one side cell, and the output restores that border cell to 5. The
sampler now teaches this branch, multiple independent boxes, and genuine
multi-cell columns. A three-residue schedule makes any three consecutive demos
refute `first_frame_only`, `preserve_damaged_border`, and `one_per_column`.

All advertised axes are exact and recoverable from pixels. The self-check is
intentionally a little broader than the sampler so that all five canonical
inputs—including examples with two separately damaged borders—are accepted.
## Current reviewer considerations

Source SHA-256: `01edade30d19ca4c865275cf0e294c054c0d6c8ae8d78f2a27f08aa37d825140`.

# Decisions for `ab8cb362ef4d`

## D1 — Keep the selected Racket authority unchanged

**Choice.** Treat rule hash `94102b577ef7` as authoritative and change only the
Python generator, validator, tests, notes, and task-local tooling.

**Rationale.** The canonical program solves all five canonical pairs, the selected
base `target_code` is byte/normalization synchronized with it, and the baseline
rule-smoke and authority stages already passed. The defect was the distribution's
model of lawful inputs, not observed rule behavior.

**Alternatives considered.** Rewriting the rule to require pristine frames would
make the baseline validator easier, but would contradict canonical examples that
repair a non-5 border overwrite. Replacing the selected rule with the much larger
archival `raw_code` was rejected because the archival source is not selected and
its textual divergence is irrelevant while execution parity holds.

**Probe/evidence.** `workspace/reference_probe.py` independently implements the
observable transform; task tests compare all five canonical pairs and 36 generated
inputs against real Racket. `checks/after/...authority_sync.json` records selected
synchronization and parity.

**Failure mode / limitation.** Bounding boxes are inferred from connected 5-cells;
pathological inputs with unrelated connected 5 structures are intentionally
rejected by validation rather than claimed as supported.

## D2 — Model a box as a color-5 component bounding box, not a pristine border

**Choice.** Detect connected color-5 components, use each component's bounding box,
permit non-5 replacement of side cells, and restore the complete border in output.

**Original rationale.** The imported baseline's pristine rectangle search appears
to have been a simplification; no retained note justifies it.

**Rationale.** Canonical inputs include non-5 cells where a side-border 5 would
otherwise be. The selected authority still identifies the box from the remaining
5-component and writes the full bounding-box border.

**Alternatives considered.** A corner-only detector was rejected because it would
accept too many unrelated rectangles. A “repair first, then search all rectangles”
heuristic was rejected as ambiguous. Component bounding boxes match the authority
and are easy to audit.

**Probe/evidence.** Canonical pair acceptance in
`tests/test_generator_review.py`; damaged-border oracle and observer in
`workspace/reference_probe.py`; semantic witness `damaged_border` refutes
`preserve_damaged_border`.

**Failure mode / limitation.** The default sampler creates at most one damaged
border cell total, while the validator accepts the broader canonical case of one
per box. This is deliberate: one generated witness is enough to teach repair
without making every example visually noisy.

## D3 — Replace eight misleading axes with six exact observable controls

**Choice.** Expose only `grid_h`, `grid_w`, `n_frames`, `n_colors`,
`column_pattern`, and `border_overwrites`.

**Original rationale.** The imported axis schema appears templated from generic
palette/texture metadata. Several controls were not read by `generate()` and
could not be recovered from pixels.

**Rationale.** Each retained control changes a property that can be measured from
the generated grid. Honest controls make stratification, override tests, and
future data ablations meaningful.

**Alternatives considered.** Keeping `palette_kind`, `position_bias`, `density`,
and `texture` as labels was rejected because fixed strings and aliases create
metadata without independent behavior. Degenerate textures (`no_frame`,
`no_pebbles`, `all_at_bottom`) were rejected from the selected distribution
because they either leave the rule undefined or create identity outputs.

**Probe/evidence.** `observe_overrides()` is independently checked against
`reference_probe.observed()` for all boundary combinations. The final override
battery executed 29,070 accepted draws with no findings and rejects unknown keys.

**Failure mode / limitation.** Exact observability constrains implementation
freedom: changing how patterns are defined requires updating both metadata and the
observer contract rather than silently changing meaning.

## D4 — Use canonical-like dimension and color ranges

**Choice.** Set `grid_h=11..16`, `grid_w=12..18`, `n_frames=1..3`, and
`n_colors=2..7` marker colors (drawn from nonzero colors other than frame color 5).

**Rationale.** Canonical input profiles are 11–13 rows, 12–15 columns, and 8–9
total colors including 0 and 5. The chosen ranges include every canonical profile,
allow meaningful lower-complexity overrides, and remain constructively feasible.
Three frames are needed to refute first-frame-only behavior strongly.

**Alternatives considered.** Retaining the baseline 7–14 × 9–16 metadata was
rejected because its lower endpoints cannot realize all advertised frame/color
combinations and its defaults missed canonical profiles. Extending to ARC's 30×30
maximum was rejected as unnecessary for this task and expensive for exhaustive
override coverage.

**Probe/evidence.** Profile floor accepted 5/5 canonical inputs and hit exact
profiles 60/60 draws. Boundary tests construct all selected combinations at
11×12.

**Failure mode / limitation.** Default data does not uniformly cover every value in
the ranges; exact overrides are the supported mechanism for cross-product studies.

## D5 — Define three column patterns by observable occupancy

**Choice.**

* `separate`: every occupied interior column contains exactly one marker;
* `stacked`: each box uses one occupied column, and the lead stack has a real gap;
* `mixed`: the lead box has a gapped multi-marker column plus another occupied
  column; later boxes may use separate columns.

**Rationale.** These patterns distinguish independent per-column gravity from two
plausible shortcuts: dropping only one value per column and assuming every marker
has its own column.

**Alternatives considered.** Purely random marker placement was rejected because
small frames often collapse to one pattern accidentally. A pattern label that
selected probabilities rather than an exact property was rejected as
non-observable. Always stacking every marker was rejected because it under-teaches
independent columns.

**Probe/evidence.** The first green attempt exposed two constructive bugs: the
smallest stack could already be stable, and a nominal mixed case could occupy one
column. Failing cases are retained in
`checks/task-tests-green-attempt1.log`; the corrected boundary matrix is green.

**Failure mode / limitation.** These are data-generation categories, not claims
that the canonical rule names such categories. The validator accepts lawful
arrangements outside the three selected construction templates.

## D6 — Use a constructive placement algorithm with deterministic fallback

**Choice.** Derive per-box minimum dimensions, prefer small randomized expansions,
place rectangles with bounded backtracking and one-cell separation, then fall back
to minimum dimensions if the preferred layout does not fit.

**Rationale.** Rejection-only placement made tight exact overrides flaky and could
silently return incomplete layouts. Construction makes every advertised boundary
combination either succeed deterministically or fail loudly before emitting an
invalid grid.

**Alternatives considered.** Unbounded random retries were rejected for
nondeterministic latency. Hand-coded layouts for every combination were rejected
as brittle and difficult to extend. Allowing touching boxes was rejected because
5-components would merge and change the rule's box decomposition.

**Probe/evidence.** 144 focused boundary combinations and 323 override-gate cases;
no generation errors in the final gate. Hash-seed independence is tested in
separate Python processes.

**Failure mode / limitation.** The search is specialized to at most three boxes.
Raising `n_frames` would require a fresh feasibility analysis rather than only a
metadata edit.

## D7 — Make the default distribution a three-residue teaching schedule

**Choice.** Cycle defaults through `(2 frames, mixed, damaged)`, `(3 frames,
separate, intact)`, and `(1 frame, stacked, intact)` profiles. Any caller override
replaces the corresponding scheduled value exactly.

**Rationale.** Individual witness frequency is insufficient: a three-demo lesson
must contain enough evidence to reject all declared rivals. The schedule gives a
hard guarantee for every consecutive three-example window while preserving
seeded variation inside each profile.

**Alternatives considered.** Independent random axes were rejected because rare
branches can disappear from a complete lesson. Putting every witness in every
example was rejected because it reduces diversity and encourages conjunction
shortcuts. A longer schedule was unnecessary for the three current rivals.

**Probe/evidence.** Focused tests check 24 cyclic starts per band; semantic gate
reports 12/12 identifiable lessons; the external census covers 100 lessons and all
six start residues per band with zero ambiguity.

**Failure mode / limitation.** The schedule itself is a positional regularity.
Current consumers do not expose `sample_index` to the model, but a shared cyclic
query-position gate is still recommended because the lesson census does not
rotate the already materialized pairs.

## D8 — Pin three executable rivals and their witnesses

**Choice.** Declare `first_frame_only`, `preserve_damaged_border`, and
`one_per_column` through `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, and
`LESSON_COMPETITORS`.

**Rationale.** Each rival is a compact, plausible rule induced by a missing branch
in the baseline distribution. Executable rivals let gates test whether examples
actually disambiguate behavior rather than trusting prose labels.

**Alternatives considered.** A long speculative rival list was rejected because
weak or answer-equivalent rivals create noisy gates. `drop_all_markers_to_global
bottom` was considered but omitted: separated frames make it easy to refute and it
was not the most direct baseline shortcut.

**Probe/evidence.** All named witness/rival claims pass; canonical pairs refute all
three; 300 lesson windows refute every declared competitor.

**Failure mode / limitation.** This remains a finite adversarial set, not proof of
unique rule induction. New model failures should be promoted into new executable
rivals only after a concrete counterexample is retained.

## D9 — Keep validator support broader than sampler support

**Choice.** `self_check` and `strict_canonical_like` accept lawful canonical cases
beyond defaults while requiring at least one movable marker and rejecting
structural corruption.

**Rationale.** A validator should recognize the task's lawful domain, not merely
reverse-engineer current sampler defaults. Otherwise canonical profile checks
become impossible and future diversification is blocked.

**Alternatives considered.** Reusing the sampler's exact observer as validation
was rejected because canonical examples can have multiple damaged boxes and
arrangements not generated by the three templates. Accepting any grid containing
5 was rejected as too weak.

**Probe/evidence.** Five canonical inputs pass; five destructive mutations and
five malformed forms are diagnostic; 600/600 generated draws pass strict checks.

**Failure mode / limitation.** The validator does not prove that every accepted
grid is the only possible interpretation under the Racket DSL. It enforces the
selected structural contract and semantic non-identity conditions.

## D10 — Build an independent reusable probe instead of testing internals only

**Choice.** Add `workspace/reference_probe.py` with canonical loading,
5-component/bounding-box analysis, a Python oracle, exact observation, rivals,
and real-Racket parity execution.

**Rationale.** Tests that call only generator helpers can agree with the same bug.
The probe derives outputs and observable properties independently and can be
reused by future agents when adding rivals or investigating model failures.

**Alternatives considered.** Importing private battery functions was rejected by
the packet contract and would couple task tests to runner implementation. Copying
canonical labels into tests was rejected because it would not generalize to fresh
generated cases.

**Probe/evidence.** 184 focused tests use the probe. Its oracle agrees with all five
canonical outputs and real Racket over 41 grids without mutating inputs.

**Failure mode / limitation.** It is still an independently written mirror of
observable behavior, so real-Racket parity remains the ultimate execution check.
