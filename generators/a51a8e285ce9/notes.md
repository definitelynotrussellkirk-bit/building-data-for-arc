# Current native extension — review-db65cf48f1dddb72

Production **4.0.0** and its approval state remain unchanged. Generator SHA-256:
`d4dd73dd6d4f6692fe9aef54d07b7373ac64f5e8cebcbc577f962573543f01a6`.
The default retains the exact **2,234-byte** canonical Racket program, SHA-256
`d76e03446f2a9f862524d84ccaa866f67dbe9ef2ad22c45cd755fb67c57211a7`.
The native extension under `workspace/parametric/` is reviewer-ready; exact-source
owner acceptance remains pending and `training_admitted=false`.

## Current rule, grammar and teaching decisions

`mode=prototype` returns the displayed matched prototype in query color, exactly
as the canonical rule does. `mode=transfer` infers the unique D4 transform taking
the matched prototype to the query and applies that transform to the other
prototype. The transfer program SHA-256 is
`08383b1fdf8e552ac508f7cda91d562f718e7e9f9c8f48d4544a0fdcddb528a1`.
A stores the matched index and transform code; B consumes the code for the other
prototype's transform/render operation. The causal control replaces only that
code with identity, leaving selection and B unchanged.

The native grammar uses exact built-in list grids, axes 1..30, exact ARC colors,
three geometric equal-width panels and full-height separators at the canonical
quotient-derived columns. A zero-only remainder of 0..2 rightmost columns is
allowed, giving a lawful 30-column canvas. Each panel has one connected monochrome
support; all three support colors differ, and color8 is valid in every role.
Both prototypes must have eight distinct D4 poses and distinct D4 classes; the
query matches exactly one. Arbitrary admitted shape sizes and holes are allowed.
Symmetric original examples remain defined by the unchanged canonical program
but are explicitly outside this transfer grammar, avoiding an arbitrary tie rule.

Supported controls are exact seeds 0..2**63-1, **4..6 demos (default four)** and
1..4 private queries (default four). Separate setting/demo/query streams build
full six-plus-four banks before slicing; inputs match across settings and count
prefixes remain stable. Four required cores cross match roles0/1 with rotation
and reflection. Two reflection cases reject rotation-only matching with fallback0/1;
two rotation cases reject reflection-only matching with those fallbacks. These
categories are disjoint for asymmetric supports, so the four-demo cost is explicit
for this rival set. Equal areas and 3x3 boxes prevent counting/bounding-box shortcuts.

Tall connected comb pairs have equal area, full eight-pose orbits and different
D4 classes by construction. Both 30x30 profiles contain substantial content:
**453 and 468 foreground cells**, including separators. These different counts
also guarantee distinct large demo/query inputs. There are no rejected draws,
label filters or retries.

## Current executed evidence

Paths below are relative to `WORK/` in this return.

- `checks/a51a8e285ce9/native-and-audit.xml` and its command receipt: **120 tests
  passed** (55 native, 65 independent audit). Expected missing-module red receipts
  are retained separately; there were no later native implementation failures.
  Independent read-only review found no Critical, Important or Minor issue.
- `checks/a51a8e285ce9/sampler-v1.json`: **96/96 requests passed** across count
  pairs (4,1), (5,4), (6,4); 160 distinct inputs, 64 distinct query inputs and
  32 distinct 30x30 inputs were observed.
- `checks/a51a8e285ce9/teaching-v1/private/audit.json` and `executions.jsonl`:
  **40 intended labels** matched generated claims, independent Python and protected
  Racket. **116 hypothesis fits** yielded 112 refutations and four intended
  survivors only; all 16 surviving query scores agree. Accounting is **520
  requests, 384 protected evaluations and 136 exact cache hits**. Task/runtime
  source hashes and live runtime identity remained unchanged. Fitting uses only
  the first four demonstrations and freezes survivors before query scoring.
- `workspace/parametric/evidence/manifest.json`: 13 source/evidence files,
  manifest SHA-256
  `b4cced0f8d3d73d375f6fe1b55f23f9e654cbeb654783823425b0d7674a5089b`.
  `checks/a51a8e285ce9/qualification/{qualification,execution}.json` qualified
  four jobs, six demos/four queries each, with **64 protected evaluations**.
- `checks/a51a8e285ce9/causal-recipe.json` and `causal/{witness,replay}.json`:
  two seed-0 cases (train0 rot90 and train2 flip-h) are `reviewer_replayed`.
  Four additional protected evaluations retain actual/counterfactual intermediate
  codes; the native builder separately constructs and replays both final outputs.
- `checks/a51a8e285ce9/preview/`: four qualified episodes produced **16 verified
  single-query public views**. Projection checks do not independently replay labels.
- `checks/a51a8e285ce9/design_transfer_probe.json`: 12 protected literal design
  evaluations cover four cores, identity-code controls, color8 in support/query
  roles and zero-only quotient tails.

These are finite seed, count and named-rival checks, not universal identifiability
or exhaustive correctness over all admitted shapes. There are no inherited audit
entries for this task. The next owner action is qualification and acceptance of
the exact integrated native source. No training admission or activation occurred.

---

# Working notes: a51a8e285ce9

## Review provenance

Assignment `review-8720adb61275e5a8`, October 3–4, 2026. No prior return was used
as a repair lead: `evidence/associated_notes.jsonl` was empty and the selected
baseline itself was measured. The canonical Racket rule was inspected only
after the required unrelated blind solve had been finished.

## Baseline defects reproduced

Baseline generator SHA-256:
`0e14ed9965d6cf380bc4b8b3d96465af8cd26d0daa9cd038230f4e16a724d2c9`.
The before battery retained under `checks/before/` had 6 passing stages, 1
advisory stage, and 5 failing stages. Root causes included:

- no pinned `RULE_HASH`;
- stale fixed-4×14 documentation that contradicted generated geometry;
- separator discovery by color rather than panel geometry, causing a canonical
  color-8 prototype to be misread as empty;
- ignored and typo-tolerant advertised overrides;
- fixed top-left object placement and weak/dead axes;
- prototype pairs with unequal areas, so counting cells usually solved the
  selection problem without learning D4 equivalence;
- no executable semantic contract or lesson-level rival check.

The first task-local RED run retained under `checks/task-tests-red/` had 38
failures and 15 passes. Those failures were intentional reproductions of the
above defects, not harness errors.

## Selected repair

Version `4.0.0` pins rule hash `d76e03446f2a` and constructs two connected,
asymmetric, same-area polyominoes from deterministic size-5–8 catalogs. Their
D4 classes are distinct and each has an eight-element orbit, so every exact
transform override is observable. The query is a scheduled D4 transform of one
prototype; both roles occur within every four-example lesson and at least one
example requires reflection rather than rotation alone. Prototype and query
objects are independently offset inside 4–7 cell panels.

Panels are recovered from width geometry (`3*panel_w+2`), not by searching for
color-8 components. This is required because palette-size 4 intentionally uses
8 as one prototype color. All exact axes are validated and round-trip through
`observe_overrides`.

The semantic contract names five rivals: always select panel 0, count cells and
choose panel 1 on a tie, rotations only, emit the query orientation, and retain
the prototype color. Equal-area match-0 examples specifically refute the
counting shortcut, which fits every usable canonical pair. The four-example
schedule and `lesson_identifiable` require all named competitors to be refuted.

`workspace/reference_probe.py` is an independent geometry/D4 oracle and Racket
parity helper. `tests/test_generator.py` contains 53 regressions covering
canonical color-8 support, rule pinning, strict overrides, schedule observability,
equal-area/asymmetric prototype construction, independent placement, malformed
fixtures, semantic witnesses, and authority parity.

## Final measurements and limits

Final generator SHA-256:
`d4dd73dd6d4f6692fe9aef54d07b7373ac64f5e8cebcbc577f962573543f01a6`.
The completed after battery passed all 12 stages; selected task tests passed
53/53. A source-bound census materialized 100 lessons per difficulty band:
300/300 complete, 1,500/1,500 unique inputs, zero ambiguous lessons, zero hook
warnings or scoring errors, and every declared rival refuted in every lesson.
The post-repair visible-only solve passed all four demonstrations on its first
revision and is honestly marked as having earlier rule exposure.

These checks establish the declared domain and rival set, not universal ARC
induction. The generator intentionally covers connected asymmetric polyominoes
of area 5–8 in panels 4–7; it does not teach symmetric shapes, disconnected
supports, more than two prototypes, nonzero backgrounds, or an exhaustive set
of conceivable shortcuts. The selected Racket authority was unchanged.
## Current reviewer considerations

Source SHA-256: `d4dd73dd6d4f6692fe9aef54d07b7373ac64f5e8cebcbc577f962573543f01a6`.

# Decisions: a51a8e285ce9

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical program unchanged and pin its normalized hash as
`RULE_HASH = "d76e03446f2a"`.

**Original rationale.** Unknown; the baseline did not pin the hash. Direct
canonical examples and authority-sync evidence showed that the selected Racket
rule already expressed the intended D4-family selection and output convention.

**Alternatives considered.** Rewrite the Racket program to accommodate the old
validator or change the task definition. Rejected because the defect was in the
Python input grammar/validator, not the authority.

**Probe.** Independent Python outputs were compared with real Racket execution
in the task tests and after battery. `rule_smoke`, `racket_lint`, and
`authority_sync` are green.

**Failure modes / limit.** The archival base-solution copy remains textually
divergent, as reported by authority sync, but selected execution parity passes.
No canonical-data file was changed.

## D2 — Parse panels from geometry, not color components

**Choice.** Require `width = 3*panel_w+2`, derive the two separator indices, and
then require those exact columns to be full-height color 8. Within each panel,
all nonzero cells—including color 8—belong to its one object.

**Original rationale.** The stale summary treated 8 as separator-only. The
baseline code generalized that assumption into validation, even though a
canonical prototype is color 8.

**Alternatives considered.** Reserve 8 exclusively for separators; search all
full-height 8 columns; special-case the canonical grid. Reserving 8 would narrow
lawful color support, searching is ambiguous, and special-casing would hide the
root cause.

**Probe.** The canonical color-8 example is accepted and evaluated correctly;
mutating either geometric separator is rejected. Tests are in
`tests/test_generator.py` and the independent parser is in
`workspace/reference_probe.py`.

**Failure modes / limit.** This grammar assumes exactly three equal panels and
two separators, matching the selected task. It does not generalize to arbitrary
panel layouts.

## D3 — Use same-area, distinct asymmetric prototype families

**Choice.** Build connected free-polyomino classes of area 5–8; select two with
distinct D4 orbits and full orbit size eight; give both prototypes the same
area.

**Original rationale.** The baseline’s fixed 3-cell versus 4-cell shapes made
cell count sufficient. The original author’s reason for different counts is
unknown; “unambiguous” in the stale summary appears to have prioritized easy
selection over teaching the intended rule.

**Alternatives considered.** Keep unequal areas and add a few equal-area edge
cases; hand-maintain a small shape table; include symmetric shapes. A partial
mixture would still let many lessons teach counting, a hand table is brittle,
and symmetric shapes make exact transform controls non-observable because
multiple transform names can yield the same pixels.

**Probe.** Tests enumerate sizes 5–8, verify connectedness, equal area, distinct
D4 classes, and eight unique transforms. The canonical-shortcut probe confirms
that `count_then_second` fits usable canonical pairs; generated match-0 examples
falsify it.

**Failure modes / limit.** Symmetric and disconnected families are omitted.
That is deliberate to make exact transforms auditable, but it narrows the task
domain and should not be mistaken for all possible symmetry puzzles.

## D4 — Schedule four demonstrations rather than rely on random witness frequency

**Choice.** Set `EXAMPLES_NEEDED = 4`; alternate match roles; interleave
rotations and reflections; ensure every four consecutive examples include both
roles and at least one reflection-only query.

**Original rationale.** Unknown; the baseline had no explicit lesson contract.
Random examples can contain witnesses in aggregate while a particular lesson
window remains compatible with a shortcut.

**Alternatives considered.** Three examples, fully random transforms, or eight
examples covering every code literally. Three cannot cheaply guarantee all
five named competitors are separated; random sampling creates unlucky windows;
eight is unnecessary overhead because asymmetric shapes let four examples
separate the declared rivals.

**Probe.** `lesson_identifiable` checks complete demonstrations. The production
census materialized 100 lessons per band and refuted every declared competitor
in every lesson. An intermediate 52/53 test run caught and corrected a
seed/index profile alias before final verification.

**Failure modes / limit.** The schedule proves only the declared four-example
window. A different sampler that ignores `EXAMPLES_NEEDED` or reorders examples
must rerun lesson-level checks.

## D5 — Vary geometry while retaining strong canonical-scale support

**Choice.** Support grid heights and panel widths 4–7. Core scheduling gives
frequent canonical 4×14 layouts while non-core dimensions vary by difficulty;
prototype sizes are difficulty scheduled from 5–8.

**Original rationale.** The stale summary claimed fixed 4×14, while the baseline
source already attempted geometry variation. The exact intended range was not
documented.

**Alternatives considered.** Return to fixed 4×14; sample all dimensions purely
at random; use larger grids. Fixed geometry encourages position/scale
shortcuts, pure random sampling can miss canonical support in small batteries,
and larger grids add blank-space cost without adding task semantics.

**Probe.** Profile-floor and diversity stages pass. Exact dimension and size
overrides round-trip through pixels; the census reports 1,500 unique inputs.

**Failure modes / limit.** Difficulty changes size/dimension schedules, not the
underlying logical rule. “Hard” is therefore a distributional label rather than
a measured model-difficulty guarantee.

## D6 — Randomize displayed orientations and independent legal offsets

**Choice.** Give each prototype an independently sampled D4 display orientation
and place all three objects at independent legal row/column offsets.

**Original rationale.** The baseline always anchored supports at the panel’s
top-left corner; no rationale was recorded.

**Alternatives considered.** Keep a shared alignment for visual simplicity or
move only the query. Rejected because either leaves translation or orientation
shortcuts that are unrelated to prototype-family matching.

**Probe.** Regression scans show row and column offsets vary independently and
outputs remain based on the displayed matching prototype, not query placement.

**Failure modes / limit.** Objects are still one connected monochrome support
per panel and never overlap separators, as required by this task grammar.

## D7 — Make palette size exact and exercise color-8 content

**Choice.** `palette_size=5` uses three nonseparator object colors plus 0 and 8;
`palette_size=4` uses 8 as one prototype color so the visible palette remains
exactly four colors. Prototype colors and query color are always distinct.

**Original rationale.** The baseline advertised palette/texture controls that
were not consistently honored and its validator implicitly prohibited object
color 8.

**Alternatives considered.** Exclude 8 from objects or define palette size as
“object colors only.” Exclusion would fail to exercise the canonical validator
edge; redefining the axis would make the pixel-observed value surprising.

**Probe.** `observe_overrides` returns the actual total palette cardinality;
all exact override cases pass and the canonical color-8 regression remains in
the suite.

**Failure modes / limit.** Color semantics are intentionally role-neutral
except for separators. The generator does not cover same-colored prototypes or
query/prototype color reuse.

## D8 — Expose six strict exact axes and reject typos

**Choice.** Exact axes are `grid_h`, `panel_w`, `prototype_size`, `match_index`,
`transform`, and `palette_size`. Values are type/range checked; unknown names are
errors; `None` delegates to the schedule.

**Original rationale.** Unknown. Baseline metadata and behavior disagreed, and
unknown keys were accepted, making experiment configuration silently unreliable.

**Alternatives considered.** Remove controls entirely or preserve compatibility
with stale names. Removing them would reduce reproducibility; silently accepting
stale names recreates the defect. No incompatible combinations are needed in
the selected ranges.

**Probe.** The override battery passes with `unknown_key_verdict = rejected` and
no findings. Task tests verify every legal value is observable and malformed
values fail.

**Failure modes / limit.** `transform` is uniquely recoverable only because the
generated shapes are asymmetric; canonical symmetric inputs may have aliases,
for which the observer returns the first deterministic code.

## D9 — Add executable semantic rivals, witnesses, and malformed fixtures

**Choice.** Declare rivals for always-first, count-then-second, rotations-only,
query-orientation output, and prototype-color output. Link each to a concrete
witness and require complete lessons to refute every competitor. Add missing
separator, empty query and ambiguous-prototype mutation fixtures.

**Original rationale.** Baseline had none; semantic gate was advisory because no
contract existed.

**Alternatives considered.** Rely on prose, validator coverage, or global
witness counts. None establishes that a complete lesson separates plausible
rules.

**Probe.** Semantic and defect-lint stages are green; 300 census lessons have no
surviving declared rivals. The RED suite proves these checks would have failed
on the baseline.

**Failure modes / limit.** Rival lists are finite and reviewer-authored. An
undeclared program can still fit the demonstrations; the audit finding on
`a2e752ad6948` is a concrete example of why cyclic lesson-window scanning should
be shared tooling.

## D10 — Retain independent probes and tests as future-agent tools

**Choice.** Keep `workspace/reference_probe.py` and 53 task-local tests rather
than only describing the fix.

**Original rationale.** The packet explicitly requested reusable tooling; the
baseline workspace contained only a placeholder README.

**Alternatives considered.** Test through generator-private helpers only or
leave one-off shell snippets in notes. Generator-private tests can repeat the
same defect, and prose cannot be replayed.

**Probe.** The portable task-test runner snapshots the tests, workspace, public
API and frozen fixtures; final result is 53/53.

**Failure modes / limit.** The independent oracle still encodes the reviewed
task interpretation and is not a formal proof. Real Racket remains the authority.
