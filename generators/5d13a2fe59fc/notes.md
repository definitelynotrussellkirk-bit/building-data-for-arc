# Working notes: 5d13a2fe59fc

## Current rule and authority

Every nonzero top-row cell is an independent seed. It paints a ray of its own
color down and right, including the seed cell, until the bottom or right edge.
Background is `0`. Repeated seed colors are lawful and do not merge or suppress
rays. The canonical Racket program is unchanged; `RULE_HASH` is pinned to
`ba0a11187d3c`.

## Resolved review finding

Prior return `review-07e1d618a0904d24:v0001` was used as the lead. All canonical
pairs use a different color for every top-row seed, so the plausible rival
`first_seed_per_color`—paint only the first seed carrying each color—fits all
four canonical input/output pairs. The retained in-domain counterexample
`counterexamples/first_seed_per_color.json` has top row
`[2,0,0,2,0,5,0,0]`; the intended rule paints both color-2 rays and the rival
omits the second. Its Racket-authority record is
`checks/assigned-counterexample/racket.json` in the review return.

## Current generator decisions

- The previous broad eight-axis declaration was replaced by four exact,
  observable controls: `grid_h` 5..10, `grid_w` 7..12, `seeds` 2..5, and
  `color_pattern` in `{distinct, repeat}`. Unknown, mistyped, and out-of-range
  controls fail loudly.
- The three-slot schedule is `repeat_left`, `repeat_right`,
  `canonical_distinct`. Thus two of every three consecutive draws are explicit
  repeated-color witnesses, while one draw preserves the canonical distinct-
  color profile. Exact overrides remain available for every declared control.
- `first_seed_per_color` is executable in `CANONICAL_SHORTCUTS`,
  `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS`; the repeated-color witness and
  `lesson_identifiable` hook make lesson failures machine-checkable.
- The validator accepts only rectangular 5..10 by 7..12 grids with 2..5
  top-row seeds, ARC colors 1..9, and zeros below the top row. Repeated colors
  are intentionally part of the strict domain.

## Evidence on current generator bytes

Generator SHA-256:
`d8477cb73cd25789cb8a53542f23324c5100b76959dd650e68f52bad87d508e1`.
The after battery is all green (12/12 stages). The fixed-seed cyclic schedule
census materialized 9/9 three-demo/one-query lessons and all 36 held-out query
rotations with zero declared-rival ambiguity. The wider production census
materialized 300/300 lessons (100 per difficulty band), 1,200 labeled pairs,
and 1,200 query rotations with zero ambiguity for the declared rival; it saw
1,177 unique exact input grids.

## Limits and open findings

These checks establish coverage against the declared
`first_seed_per_color` rival, not universal rule identifiability. The schedule
census fixes one seed and the 300-lesson census samples finite random support;
neither proves every lawful input or every conceivable shortcut is covered.
The repair intentionally narrows the advertised surface to controls that are
actually observable; it does not restore the old dead palette/anchor/asymmetry
metadata. No Racket-rule change was justified.
## Current reviewer considerations

Source SHA-256: `d8477cb73cd25789cb8a53542f23324c5100b76959dd650e68f52bad87d508e1`.

# Decisions for 5d13a2fe59fc

## D1 — Preserve the canonical Racket rule

**Original choice:** The baseline used the canonical rule “every nonzero top-row
seed paints its own down-right diagonal.” The original rationale was not recorded
in task notes, but it matches all canonical pairs.

**Decision:** Keep the rule text unchanged and pin `RULE_HASH = "ba0a11187d3c"`.

**Alternatives considered:** Change same-color rays to merge, suppress later
seeds, or add collision stopping. Each alternative contradicts the written rule
or creates unnecessary authority drift.

**Probe/evidence:** Canonical authority smoke and synchronization are green in
`checks/after-final/`; the exact repeated-color witness was evaluated with the
public Racket `apply` command in `checks/assigned-counterexample/racket.json`.

**Failure modes/limits:** `rule_mirror` is not authority. A future canonical rule
change must update the pinned hash and rerun authority-bound checks.

## D2 — Replace the dead eight-axis surface with four observable controls

**Original choice:** The baseline advertised dimensions, seed count, palette,
anchor/asymmetry, and other axes. Several were absent, accepted silently, or
could not be probed. The rationale for those declarations is unknown.

**Decision:** Advertise only `grid_h`, `grid_w`, `seeds`, and `color_pattern`.
Every accepted override has an exact observable consequence, and unknown keys
fail loudly.

**Alternatives considered:** Retain compatibility aliases, mark dead axes as
“diagnostic,” or implement all historical palette/anchor controls. Those choices
would preserve misleading API surface or add behavior unrelated to the teaching
defect.

**Probe/evidence:** Baseline override diagnostics are in
`checks/before/checks/5d13a2fe59fc_before_battery_summary.json`; final override
checks are green, and task tests cover exact minimum, maximum, middle, wrong-type,
out-of-range, and unknown-key cases.

**Failure modes/limits:** This is an intentional API contraction. Downstream code
that relied on silently ignored historical keys should now fail and be corrected.

## D3 — Use 5..10 rows, 7..12 columns, and 2..5 seeds

**Original choice:** Canonical examples use 5..8 rows, 7..10 columns, and 2..3
seeds. The old generator’s effective bounds and their rationale were partly
obscured by dead axis metadata.

**Decision:** Keep a canonical-sized core while broadening moderately to 10×12
and five seeds. Require at least two seeds so the independent-seed concept is
visible.

**Alternatives considered:** Allow one seed, allow all nine colors/seeds, or use
very large grids. One seed cannot expose the identified shortcut; dense or much
larger grids add visual clutter without a new rule distinction.

**Probe/evidence:** Profile-floor, diversity, self-check, and strict-profile
stages are green. Thirty deterministic probes in the task tests produced at
least 28 unique exact grids and both color patterns.

**Failure modes/limits:** The generator does not cover every structurally lawful
size or seed count. Those omissions are distribution limits, not validator claims
about the mathematical rule beyond this task’s selected training domain.

## D4 — Schedule two repeated-color profiles and one distinct-color profile

**Original choice:** Canonical demonstrations and the prior sampler used distinct
colors, leaving `first_seed_per_color` viable. Prior return
`review-07e1d618a0904d24:v0001` identified the issue.

**Decision:** Use a period-three sequence: repeated color at the left extreme,
repeated color at the right extreme, then a canonical-style distinct draw. Any
three consecutive draws contain at least two witnesses.

**Alternatives considered:** Pure random repetition, all-repeat generation, or
hand-inserting one fixed counterexample. Random repetition offers no complete
lesson guarantee; all-repeat drops canonical-profile support; one fixed witness
would reduce diversity and invite memorization.

**Probe/evidence:** The task-local consecutive-window tests enumerate seeds,
bands, and cyclic starts. `checks/schedule-census.summary.json` checks all three
starts in all three bands and every query rotation; the 300-lesson census checks
broader random support.

**Failure modes/limits:** The declared schedule period is deterministic. It is
safe only because the profile index is not visible and lesson rotations remain
identifiable. A future assembler that skips or reorders samples must rerun the
source-bound census under its actual policy.

## D5 — Make the shortcut executable rather than documentary

**Original choice:** The baseline had no semantic witness, rival, or lesson hook.
Comments alone could not fail a check when a lesson remained ambiguous.

**Decision:** Implement `first_seed_per_color`,
`repeated_color_seeds`, `WITNESS_RIVALS`, and `lesson_identifiable`, and expose
the rival through all supported declaration namespaces.

**Alternatives considered:** A test-only rival or a free-form note. Those would
not be exercised by the shared semantic gate or lesson census.

**Probe/evidence:** The rival fits all four usable canonical pairs, differs on the
retained counterexample, and is refuted in every production and rotated lesson
reported by both censuses.

**Failure modes/limits:** This contract covers one named hypothesis. It should be
extended when a new plausible rival is found rather than interpreted as a proof
of uniqueness.

## D6 — Retain a minimal source-bound counterexample

**Decision:** Store the 6×8 repeated-color case in
`repo/generators/5d13a2fe59fc/counterexamples/first_seed_per_color.json` and
cover it with a portable task-local regression.

**Why this case:** It is small, accepted by the final validator, contains two
seeds of color 2 plus a control color 5, and yields visibly different intended
and rival outputs.

**Probe/evidence:** The regression binds the record to the current generator
SHA-256 and rule hash, recomputes both outputs independently, and checks the
outputs differ. The Racket output is retained separately under `checks/`.

**Failure modes/limits:** The JSON’s source hash intentionally makes source drift
fail the regression; a legitimate future generator edit must regenerate or
explicitly update the record after rechecking it.
