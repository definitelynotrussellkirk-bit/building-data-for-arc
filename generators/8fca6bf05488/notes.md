# Working notes: 8fca6bf05488

## Review result

The imported `1.1.0` generator had no `RULE_HASH`, advertised controls that were
inert or overlapped, accepted unknown override keys, declared dimension ranges
it did not honor, generated invalid “textures,” and had no executable semantic
contract. Its checker also accepted a short horizontal two-cell impostor. The
before battery recorded 7 green, 2 advisory, and 3 failed stages.

Version `2.0.0` is a focused generator rewrite; the canonical Racket authority
is unchanged. It has five exact observable axes (`grid_h`, `grid_w`, `emitters`,
`palette_kind`, `profile`) and four mutually recognizable teaching profiles.
Every advertised Cartesian override combination is constructible.

## Curriculum

A deterministic four-slot schedule guarantees that every ordinary four-demo
window contains:

1. a canonical-like distinct-column case;
2. a stacked-column overwrite case;
3. a bottom-edge source case; and
4. a repeated-color case.

The three noncanonical profiles refute shortcuts that fit all five canonical
pairs: keep only the top source per column, ignore non-unique colors, and drop
bottom-row sources. Canonical draws use one of three source-like shape/palette
anchors in every difficulty band; difficulty changes nuisance scale and default
emitter count, not the legal override domain.

## Verification retained

- TDD red: 9 expected failures, 1 pre-existing pass (`checks/tdd-red.log`).
- Focused tests: 10/10 pass (`checks/task-tests/`).
- Complete after battery: 12/12 stages green (`checks/after/`).
- Source-bound census: 300/300 lessons, 0 declared ambiguities, 1,498 unique
  inputs (`checks/lesson-census.json`).
- Reusable cyclic probe: 144/144 lessons, 0 failures
  (`checks/shortcut-probe.json`).

## Limits

The declared rival set is finite and cannot prove unique human induction. The
selected teaching grammar intentionally covers 6–12 rows, 7–12 columns, 2–4
sources, and two four-color palettes rather than every input the abstract Racket
program could execute. No prior retained return was used as a design lead; the
current baseline, canonical pairs, and measured gates were used directly.
## Current reviewer considerations

Source SHA-256: `ac267d4d49ac688b6ddc15b61e9a3615b15d104a4dd0d1bb74730c3f08ca88e0`.

# Decisions for 8fca6bf05488

No prior retained return was used as a design lead. Decisions below come from the
selected baseline, all five canonical pairs, the authoritative rule, and measured
before/after evidence.

## D1. Preserve the canonical Racket authority

**Choice.** Keep rule hash `fe26cc0d2dfe` and repair only the generator,
validation, tests, and executable semantic contract.

**Rationale.** The Racket rule matched every canonical output and authority-sync
already passed. The failures were in sampling and contracts, not labels.

**Rejected alternatives.** Simplifying the rule to one source per column, or
changing overwrite order, would fit the narrow canonical geometry but alter the
selected authority.

**Probe.** The Python mirror is pinned against all 5 canonical pairs; final
`rule_smoke`, `racket_lint`, and `authority_sync` pass.

**Limit.** Mirror parity on a finite set does not replace the Racket authority.

## D2. Replace inert controls with five exact observable axes

**Choice.** Advertise only `grid_h` (6–12), `grid_w` (7–12), `emitters` (2–4),
`palette_kind` (`low|high`), and `profile` (four values). Reject unknown keys and
bad types/ranges. Keep `texture` only as a validated compatibility alias to
`profile`.

**Rationale.** Baseline metadata claimed controls such as density, texture,
palette size, and distinct-color count that were dead, overlapping, or not
honored; dimension overrides produced thousands of mismatches.

**Rejected alternatives.** Retain every old axis with hidden incompatibilities;
clamp invalid requests; or silently ignore unknown keys. All make provenance
unreliable.

**Probe.** All 64 boundary Cartesian combinations are constructed and observed;
the final override gate has zero findings and rejects an unknown key.

**Failure mode.** The exact domain is intentionally narrower than every input the
abstract transformation could accept.

## D3. Teach four mutually recognizable semantic profiles

**Choice.** Use `canonical`, `stacked`, `bottom_boundary`, and `repeated_color`.
Each profile changes one rule-relevant branch while holding the sparse source
language recognizable.

**Rationale.** All canonical pairs have distinct columns, unique colors, and no
bottom source. Consequently, “topmost source only,” “unique colors only,” and
“drop bottom source” fit all five canonical pairs.

**Rejected alternatives.** Random sparse emitters without branch guarantees;
invalid negative textures; or only canonical-like examples. Randomness can miss
the exact witnesses in short lessons, and invalid inputs do not teach the rule.

**Probe.** Each profile has nonoverlapping observables and an exact named rival.
The 300-lesson census refutes every declared rival in every lesson.

**Failure mode.** These are finite hand-selected rivals, not an exhaustive model
of every shortcut Qwen3.5-9B might learn.

## D4. Guarantee branch coverage with a four-slot schedule

**Choice.** `sample_index % 4` cycles the four profiles; every consecutive
four-demo window therefore includes all profiles. Seed affects layouts, not the
profile order.

**Rationale.** Training quality is lesson-level: high marginal witness frequency
is insufficient if a query contains the only branch witness and demos omit it.

**Rejected alternatives.** Independent random profile sampling or a long schedule
with only aggregate balance. Both allow locally ambiguous lessons.

**Probe.** Task tests check every cyclic start in a 12-start span. The reusable
probe checks 144 windows (3 bands × 3 seeds × 16 starts), all clean.

**Failure mode.** Downstream assembly must preserve consecutive four-demo windows;
a different sampler should rerun the probe under its actual assembly policy.

## D5. Retain canonical-size support in every difficulty band

**Choice.** Canonical-profile defaults choose one of `(6,10)`, `(7,8)`, or
`(9,7)` and two sources, yielding one of the canonical shape/palette-size
profiles in every four-draw cycle. Noncanonical profiles use band-aware size and
2/3/4 source defaults.

**Rationale.** The baseline had no exact canonical-profile hits in medium/hard,
triggering profile-floor advisories.

**Rejected alternatives.** Force every draw to a canonical size or make exact
shape a public composite axis. The former reduces diversity; the latter adds no
semantic control needed by training.

**Probe.** Each band gets at least 5 canonical-profile hits in 20 draws; final
profile-floor passes.

**Failure mode.** Difficulty changes nuisance complexity more than reasoning
composition.

## D6. Make `self_check` describe the teaching manifold

**Choice.** Require rectangular 6–12 by 7–12 integer grids, colors 0–9, 2–4
sources on at least two rows, and exactly one declared profile.

**Rationale.** The old checker accepted a short horizontal two-cell impostor and
contradicted its own advertised degenerates.

**Rejected alternatives.** Validate only broad Racket executability, or accept
invalid negatives as ordinary textures. Both make strict-fraction and override
evidence meaningless.

**Probe.** A targeted impostor fails; all canonical inputs and generated profile
inputs pass; strict fraction is 1.0.

**Failure mode.** Lawful but off-curriculum source arrangements are rejected by
design.

## D7. Add an executable semantic contract

**Choice.** Provide a canonical-bound Python mirror, observables, witnesses,
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and
`lesson_identifiable`.

**Rationale.** The baseline semantic stage could only report `NO_CONTRACT`, so it
could not distinguish correct labels from underdetermined lessons.

**Rejected alternatives.** Prose-only rationale or a test that checks outputs
without rival survival. Neither is reusable by shared gates.

**Probe.** Semantic gate passes; all three canonical shortcuts fit 5/5 canonical
pairs; census and cyclic probe find no surviving query-changing rival.

**Failure mode.** New plausible rivals must be added as they are discovered.

## D8. Use two disjoint palettes without making color identity semantic

**Choice.** Low `{1,2,3,4}` and high `{6,7,8,9}` palettes are exact controls;
colors are sampled within a profile and never determine the transformation.

**Rationale.** This gives obvious palette variation while keeping source colors
literal and avoiding background 0.

**Rejected alternatives.** Arbitrary subsets of 1–9, a claimed palette-size
axis, or mixed palettes. Those complicate observability without teaching a new
rule branch.

**Probe.** `palette_kind` is inferred exactly from every generated grid, and all
boundary override combinations pass.

**Failure mode.** Cross-band palette mixing is not represented; it is irrelevant
to the selected rule but could be added as a new explicit profile if needed.

## D9. Build a reusable source-bound shortcut probe

**Choice.** Add `workspace/shortcut_probe.py`, which imports rival declarations,
checks their canonical fit, tests cyclic lesson windows, records exact witness
cells, and can fail CI via `--assert-clean`.

**Rationale.** Future edits should not require reconstructing the review logic or
copying a stale rival list.

**Rejected alternatives.** A one-off notebook/console transcript or hard-coded
rival names. Neither is durable or source-bound.

**Probe.** Retained report `checks/shortcut-probe.json`: 144 lessons, 0 failures,
all rivals have witnesses.

**Failure mode.** Python-mirror results depend on the separately verified parity
and remain finite-sample evidence.
