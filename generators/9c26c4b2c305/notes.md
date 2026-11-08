# Working notes: 9c26c4b2c305

## Current exact-width control

`grid_w` accepts exact Python integers 4..14; `None` retains the scheduled
default. The explicit override now uses the existing `draw_int_strict` helper.
The previous permissive draw silently accepted `4.0`, `4.75`, `14.0`, `14.75`,
`"4"`, and `"14"`, including truncating the out-of-domain `14.75` to 14.
The focused regression failed on those six cases before the one-line repair
and passed all 13 cases afterward, including integer bounds and the `None`
convention. Evidence: `checks/9c26c4b2c305-review/before/pytest.xml` and
`checks/9c26c4b2c305-review/after/pytest.xml`.

`VERSION` remains 3.1.0 so lawful requests keep their keyed random layouts.
The bounded source-bound probe confirms identical input bytes for all 18
fixed recipes before and after, covering all four scheduled slots and width
endpoints 4 and 14 in each difficulty band. All 18 labels were executed through
the unchanged canonical Racket rule and matched the Python mirror. Baseline
source: `8ffed236db06f9606aa5f45c3642e406f9e6293b1b8d678df73db2c318ed1e45`;
repaired source: `057b07ba5c0c99a593b73ba3f82fac300bfe3ae699231ca4e0b86102ec50b84f`.
Evidence: `checks/9c26c4b2c305-review/before/probe.json` and
`checks/9c26c4b2c305-review/after/probe.json`; reproducer:
`workspace/width_control_probe.py`.

This secondary-target check covers the width control only. The earlier
curriculum, authority, and palette semantics are preserved; no parametric
variant, full battery, or new teaching census was run for this repair.

## Review outcome — version 3.1.0

The imported version 3.0.0 had a curriculum gap, not an authority-rule defect.
All canonical examples and every default palette used distinct top and bottom
foreground colors. The canonical-fitting conditional rule
`same_color_xor_otherwise_or` therefore behaved as OR on every observed lesson
but could switch to XOR whenever the panel colors were equal.

A source-bound baseline census over 100 four-example lessons in each of easy,
medium, and hard (1,200 generated inputs total; generator SHA-256
`7d197f84c9bd09d7f131aab534eaee3244698648c7cf007413e64c0b759efb30`)
found zero equal-panel-color inputs. The conditional rival disagreed on zero of
1,200 inputs and survived 300/300 complete lessons. Evidence:
`checks/baseline-same-color-gap.json`.

Version 3.1.0 makes the smallest distribution repair:

- adds exact observable palette profile `same_color_779 = (7, 7, 9)`;
- schedules it in slot 1 of every four-example curriculum window while retaining
  the prior `high_789` profile as an explicit override for compatibility;
- declares the canonical-fitting conditional rival in both
  `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`;
- adds a same-color semantic witness and requires every complete lesson to
  contain same-panel-color evidence; and
- adds three task-local regressions covering override observability, every cyclic
  four-slot start, canonical fit, and lawful refutation.

The authority rule itself remains occupancy OR. No canonical row or Racket
behavior changed. The active base solution's `target_code` initially differed
from canonical only in formatting, causing the final `authority_sync` stage to
fail despite execution parity. It is now copied exactly from canonical;
archival `raw_code` remains preserved and execution-parity checked.

## Test-first record

The three new unique tests were added before the generator change. In the
portable task-test layout they failed in both copied locations, yielding 6
failures and 12 pre-existing passes. Evidence:
`checks/red-task-tests/result.json`.

After the repair the same portable stage passed 18/18 executions (nine unique
test functions, copied to two runtime paths). Final evidence:
`checks/task-tests/result.json` and `checks/task-tests-console.log`.

The complete after battery passed all 12 stages: lint, self-check, rule smoke,
defect lint, distribution gate, profile floor, semantic gate, diversity,
override, grammar, Racket lint, and authority synchronization. Evidence:
`checks/after/checks/9c26c4b2c305_after_battery_summary.json`.

## Source-bound lesson census

`workspace/lesson_probe.py` dynamically reads the generator's actual
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`; it does not copy a rival-name
list. It verifies every declared canonical shortcut against all five usable
canonical pairs, then samples 100 complete four-example lessons in each band.
All four cyclic starts appear 25 times per band.

On final generator SHA-256
`8ffed236db06f9606aa5f45c3642e406f9e6293b1b8d678df73db2c318ed1e45`:

- 300/300 lessons were identifiable;
- all 1,200 generated inputs were exact-byte unique;
- every lesson contained one equal-panel-color input;
- all nine declared rivals were killed in every lesson; and
- `fixed_width_four`, `fixed_palette_124`, and
  `same_color_xor_otherwise_or` each fit 5/5 canonical pairs before being tested
  against generated lessons.

Evidence: `checks/lesson-probe/final.json`. This finite census is not a proof
against every possible learned shortcut.

## Post-repair solve

The exposed solve was prepared from the final generator bytes. Revision 1
mistook the first fully occupied panel row for the divider and produced a genuine
execution failure. Revision 2 selected the centered solid row and passed 4/4
visible demonstrations. Earlier rule exposure was declared `yes`; no Racket or
reference solution was consulted during the solve episode. See `solve/`.

## Remaining limits

- The schedule is deliberately deterministic rather than IID.
- The palette domain is finite. The equal-color curriculum uses one named color
  tuple, so the census refutes the broad equality-conditional rival but does not
  prove invariance to every hypothetical equal-color recoloring outside the
  declared profiles.
- Exact-byte uniqueness does not quotient color or geometric symmetries.
- Only declared competitors and four-example lessons were exhaustively checked.

Imported associated notes retain their original evidence and timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `057b07ba5c0c99a593b73ba3f82fac300bfe3ae699231ca4e0b86102ec50b84f`.

# Decisions for 9c26c4b2c305

## D1 — Treat equal panel colors as a lawful distribution dimension

**Input choice.** Add one named profile, `same_color_779 = (7, 7, 9)`, where
both panels use color 7 and the separator uses 9.

**Baseline rationale.** The imported source accepted structurally valid
same-color panels but its finite palette schedule never emitted one. The
original reason for keeping all panel colors distinct is not recorded; the
canonical data itself only demonstrates distinct colors.

**Probe.** The frozen baseline produced zero equal-color inputs in 1,200 draws.
The rule “XOR if equal, OR otherwise” fit all five canonical pairs and survived
300/300 complete lessons. A lawful same-color balanced grid makes it disagree
with the authority on overlap cells.

**Alternatives considered.** (1) Restrict `strict_canonical_like` to distinct
colors; rejected because that would shrink the already accepted structural
domain solely to hide a teaching gap. (2) Change the Racket rule; rejected
because authority OR already handles equal colors correctly. (3) Replace the
finite palette system with arbitrary raw colors; rejected as unnecessary and
likely to weaken exact override observability.

**Failure modes / limit.** One named equal-color tuple does not prove complete
recoloring invariance. The final report states this explicitly.

## D2 — Put the counterexample in every complete lesson

**Input choice.** Replace schedule slot 1's default `high_789` profile with
`same_color_779`; retain `high_789` in `PALETTES` and `AXES` for explicit use.

**Rationale.** Lessons require four examples and the schedule has four slots.
One same-color slot per cycle means every consecutive four-example window,
regardless of cyclic start, contains the necessary counterexample while the
other slots retain canonical palette/width, green-in-input, full-range palette,
and noncanonical widths.

**Probe.** The final census exercised all four starts 25 times per band. Every
one of 300 lessons contained same-color evidence and killed the conditional
rival.

**Alternative.** Randomly sample same-color cases at low probability; rejected
because witness frequency would not guarantee witness presence in each lesson.

**Failure mode.** The deterministic schedule is not IID and may expose its own
position regularity. That structure is accepted because lesson-level semantic
coverage is the higher-priority contract.

## D3 — Make the shortcut executable and regression-tested

**Input choice.** Add `same_color_xor_otherwise_or` to both
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, add a same-color witness, and
make `lesson_identifiable` require at least one same-color demonstration.

**Rationale.** A prose warning would not prevent recurrence. Executable rivals
let the task tests, semantic gate, and retained probe establish both canonical
fit and generated refutation.

**Test-first evidence.** The new tests failed against version 3.0.0 before the
production edit and pass against 3.1.0. See `checks/red-task-tests/` and
`checks/task-tests/`.

**Failure mode.** The declared list is necessarily finite; unknown shortcuts
remain possible.

## D4 — Preserve authority behavior and synchronize active text

**Input choice.** Leave the canonical program and `RULE_HASH` unchanged. Copy
the canonical `program_solution` text exactly into the active base
`racket_target.target_code`; retain `raw_code` as archival history.

**Rationale.** The first complete after battery showed execution parity but
failed exact active-authority synchronization. Formatting-equivalent active
sources still create reproducibility ambiguity.

**Alternatives.** Ignore the diagnostic because outputs matched; rejected
because exact source identity is an explicit acceptance gate. Rewrite canonical
to match the compact target; rejected because the base target, not canonical,
was the divergent selected copy.

**Result.** Final `authority_sync` passes and reports only the intentionally
archival `raw_code` as divergent.

## D5 — Retain a source-bound lesson census for future agents

**Input choice.** Add `workspace/lesson_probe.py` and document its command.

**Rationale.** The built-in semantic smoke sample is intentionally small. The
probe reads the final generator's rival declarations dynamically, checks all
canonical pairs, tests every cyclic lesson start, records exact source hashes,
and samples 100 lessons per band.

**Alternatives.** Hard-code expected rival names in an external script; rejected
because it can silently go stale. Use isolated witness frequency only; rejected
because individual hits do not prove complete lessons contain the witness.

**Limit.** The tool uses an independent Python OR oracle rather than invoking
Racket for all 1,200 draws. Rule smoke and authority synchronization separately
bind that oracle to the unchanged canonical authority.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/9c26c4b2c305/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D6 — Native alignment-policy parametric family (reviewer-ready)

**Design.** Add a task-local native adapter with one episode-fixed parameter,
`alignment_policy`: exact canonical `aligned`, unconditional `reflect_bottom`,
and `top_heavier_reflect_bottom`. The third setting counts occupied cells in
both panels and uses the Boolean `top_count > bottom_count` to choose the bottom
coordinate before the final occupancy OR. The production generator and canonical
Racket authority remain unchanged.

**Teaching repair.** The minimum two demonstrations now share width 4 and the
same palette while exercising opposite count branches. During self-review, an
earlier draft leaked the decision through palette, then through width parity;
both correlations were removed before the source inventory was frozen. The
retained protected-Racket audit rejects five finite rivals: canonical-aligned,
always-reflected, reversed gate, separator/palette-conditioned, and even-width
reflection. This is bounded evidence, not a uniqueness proof over all programs.

**Bounds and stress.** The adapter accepts 2–6 demonstrations and 1–8 queries;
the qualification uses three demonstrations and four distinct queries. Inputs
are matched across settings. The first four queries use widths 18, 21, 27, and
30. A square 30×30 input is not lawful because this task grammar has a fixed
height of nine rows; the separate family therefore exercises the lawful 9×30
boundary with substantive panel content.

**Native evidence.** Seeds 71 and 83 qualified all three settings through
protected Racket with three demonstrations and four queries per job. The exact
current source binding matches the returned qualification. The sequential
witness retains a bottom-heavy width-27 case and top-heavy width-30 case; changing
only the count-comparison intermediate changes final outputs in both cases.

**Status and next action.** Reviewer status is `ready`, not accepted. Training is
not admitted. The owner must integrate these exact bytes, rerun native
qualification and protected witness replay, then perform fresh native acceptance.
