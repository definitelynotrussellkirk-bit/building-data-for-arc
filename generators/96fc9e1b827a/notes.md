# Working notes: 96fc9e1b827a

## 2026-10-07 review repair

Baseline source hash: `ef476fc7fb9f6738e596651b9f24de965dee4b65bf717df97f29db70c626335d`.
Final generator hash: `25ca3f14554efa28e82b60c8fd8576ece2e605e706de10e5f600aa71952dd2eb`.
Canonical rule hash: `0fb26a20e01c` (unchanged).

The baseline battery had four blocking stages: lint, self-check, defect lint, and
override contract. Its validator accepted every destructive mutation, controls
were difficulty-subrange dependent or silently ignored, and the sampler did not
provide an executable semantic contract. The canonical demonstrations also admit
three strong object-selection shortcuts: choose the leftmost object, widest
object, or largest bounding box.

The repair replaces retry-heavy random placement with a constructive three-object
layout and a deterministic four-slot curriculum. Slot 0 supplies canonical-scale
support; slots 1–3 put the true largest-by-cell-count object away from the left and
add a strictly smaller decoy that is both wider and larger by bounding-box area.
The target family keeps exact canonical masks and adds connected skyline profiles
of 8–11 cells, 3–5 columns, and nonuniform column counts. Color 8 remains output-only.

`self_check` now enforces the actual legal domain, `strict_canonical_like` measures
canonical support, exact axis observations are replayable, and the declared rivals
are executable. The four-pair schedule is checked under every cyclic query holdout.

Final evidence:

- `checks/after-final/checks/96fc9e1b827a_after_battery_summary.json`: 12/12 green.
- `checks/task-tests-probe-green/result.json`: 11/11 task-local tests pass.
- `checks/lesson-census-final.json`: 300 lessons, 1,200 pairs, 1,200 rotations,
  zero declared-rival ambiguity, 1,183 unique inputs.
- `workspace/shortcut_probe.json`: canonical shortcut fit and emitted witnesses.
- `checks/question/leftmost-counterexample/`: exact Racket-labelled rival witness.

Limit: declared-rival tests are finite and do not prove uniqueness against every
possible human-invented rule. Output diversity is necessarily lower than input
diversity because many lawful objects share the same column histogram.
## Current reviewer considerations

Source SHA-256: `25ca3f14554efa28e82b60c8fd8576ece2e605e706de10e5f600aa71952dd2eb`.

# Design decisions for 96fc9e1b827a

## D1 — Preserve the authority; repair the generator

The selected Racket program already maps all canonical examples correctly and its
rule hash is `0fb26a20e01c`. The failures were generator/contract defects, so the
canonical row was left byte-for-byte unchanged. Alternative rejected: changing the
rule to match the old narrow sampler would have reduced the task and invalidated
canonical authority.

## D2 — Make “largest” unambiguously mean cell count

Every lawful scene contains exactly three separated monochrome objects, one unique
winner by cell count. The target has 8–11 cells; distractors are strictly smaller.
This makes the intended selection mechanically checkable and avoids tie semantics.
Alternative rejected: retaining random blob retries, because the old validator did
not prove uniqueness and could admit accidental ties or malformed objects.

## D3 — Use a four-slot teaching schedule

`sample_index % 4` chooses one exact/canonical anchor and three shortcut rebuttals.
Anchors keep measured canonical support. Rebuttal slots move the true winner to the
right or bottom and place a smaller object on the left whose width and bounding-box
area exceed the winner's. This one construction refutes all three canonical-fitting
rivals without relying on rare random luck.

The schedule is deterministic but the dimensions, target profile, placement choice
in slot 3, and palette remain seeded. The source-bound probe tests starts 0–3 across
all bands and all four query holdouts; the larger census samples 100 production
lessons per band. Alternative rejected: independent random examples, because a
three-demo lesson could easily omit the one witness needed to disambiguate selection.

## D4 — Retain exact canonical masks and add skyline morphology

Slot-0 anchors use the canonical C, staircase, or pyramid selected-object masks.
Other slots use bottom-aligned connected skyline masks with nonuniform 3–5-column
profiles and 8–11 cells. This preserves the rule-relevant column-count concept while
increasing input and output support. Alternative rejected: arbitrary polyominoes in
this repair, because they add morphology breadth without improving the central
selection lesson and make exact constructive shortcut decoys harder to guarantee.

## D5 — Canonical-scale dimensions with bounded expansion

The legal control domain is 10–18 rows and 17–24 columns. Defaults stay close to
canonical dimensions by difficulty, while every fourth draw uses an exact canonical
dimension/profile anchor. Measured exact profile support is easy 16/20, medium
12/20, hard 5/20. Alternative rejected: only canonical dimensions, which would
create a size shortcut; also rejected: broad uniform dimensions with no anchors,
which caused the baseline profile-floor advisory.

## D6 — Keep cyan output-only and vary object colors

Input object colors are three distinct samples from `{1,2,3,4,5,6,7,9}`. Color 8
is reserved for output, matching the canonical role and preventing input color from
leaking the selected object. Alternative rejected: letting target color or numeric
rank encode winner identity.

## D7 — Expose only exact, observable controls

The five axes are `grid_h`, `grid_w`, `target_shape`, `target_slot`, and
`distractor_style`. Every legal joint combination is constructively supported,
observed from the generated grid, and verified across 25,020 official draws.
Unknown keys and wrong types raise. Alternative rejected: preserving nominal
palette/texture controls that did not affect generated semantics.

## D8 — Full validator rather than acceptance-only checks

`self_check` validates rectangular ARC values, dimensions, modal background,
exact object count, distinct colors, a unique largest object, supported target
morphology/profile, strict distractor size, object clearance, output structure, and
requested control observations. Six task-specific malformed fixtures supplement
the shared mutation battery. Alternative rejected: checking only marker counts or
assuming constructive generation makes validation unnecessary.

## D9 — Declare executable rivals and limits

`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS` point to the
same executable implementations for leftmost, widest, and largest-box selection.
The probe iterates these declarations rather than duplicating names. Finite passes
only show that these declared rivals are refuted on measured lessons; they do not
prove unique human induction or coverage of undeclared hypotheses.

## D10 — Evidence and solve policy

The final battery requires query rotations. The large census uses 3 demonstrations,
1 query, 100 lessons per band, and `rotation_policy=require`. The post-repair solve
was prepared after the final generator hash, then completed using only its visible
challenge; prior exposure is recorded as yes and reference consultation during the
episode as no.
