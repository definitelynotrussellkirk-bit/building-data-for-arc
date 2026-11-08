# Working notes: d2f386d0e071

## 2026-09-28 review

### Canonical facts

- Selected rule: `(overlay g (flip-lr g))`; normalized rule hash
  `f48a460c6519`.
- Five canonical inputs have dimensions 7×9, 6×8, 8×7, 7×10, and 9×9.
- Therefore even widths are lawful; the axis is between columns on those rows.
- The 8×7 canonical input has a non-zero source on the center column, where
  left/right reflection is a no-op.
- Every canonical input has four source cells, four non-zero colors, blank
  off-axis mirror destinations, and at least two source distances from the
  midline.

### Baseline defects reproduced

- `self_check` rejected three of the five authoritative inputs: both even-width
  examples and the odd-width centerline example.
- The generator omitted `RULE_HASH` and a Python oracle.
- Seven declared axes were inert, singleton, aliases, or absent from draw
  provenance; unknown override keys were silently accepted.
- Default generation was odd-width-only and never produced a centerline source.
- No semantic contract tested whether generated lessons ruled out plausible
  shortcuts.

### Repair

Version 3.0.0 replaces the phantom axis surface with four exact observable
axes. A four-step schedule covers odd/no-center, even/narrow,
odd/centerline, and even/wide profiles; the odd/no-center branch alternates
between 7×9 and 9×9, so all five public dimension profiles are represented.
All default profiles use exactly four non-zero colors, preserving the public
palette-size profile while difficulty changes source count.

The local oracle implements flipped-grid-wins overlay semantics, not merely a
left-to-right loop. Seven named rivals and matching witnesses cover the major
shortcut classes. Four consecutive demonstrations include every scheduled
branch, and `lesson_identifiable` checks whether any named competitor can fit
all demonstrations while changing the query answer.

### Focused regression suite

`tests/test_generator_d2f386d0e071.py` pins all canonical pairs, the rule hash,
Cartesian override boundaries, unknown-key rejection, schedule coverage,
determinism/global-RNG purity, witness/rival disagreement, sliding lesson
identifiability, and structural impostor rejection.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b67c46be44d6eda86412430048b8716e5212e840750a7140b26599ae550f12b7`.

# Design decisions: d2f386d0e071

## 1. Preserve the selected rule and canonical data

**Original rationale:** The imported notes described completing a vertical
mirror, and baseline rule smoke already showed the selected Racket program
executed reliably. The problem was the generator contract, not the rule.

**Decision:** Keep `(overlay g (flip-lr g))` and pin it with
`RULE_HASH = "f48a460c6519"`. Add an independent Python oracle rather than
editing authority data.

**Alternatives considered:** Rewrite the Racket source; change canonical rows;
implement a simpler left-to-right loop without respecting overlay order.

**Probe:** All five canonical outputs match `rule_mirror`; final rule smoke is
120/120 with 120/120 mirror agreement; authority synchronization passes.

**Failure modes / limitations:** The Python oracle is a parity check, not a new
authority. Arbitrary conflicting inputs depend on overlay order, though the
lawful generator intentionally leaves destinations blank.

## 2. Accept both width parities

**Original rationale:** The old generator forced odd widths to create an
explicit center column. That rationale was contradicted by two authoritative
even-width examples.

**Decision:** Treat the axis as the mapping `c -> width - 1 - c`. On even
widths it lies between columns; on odd widths it passes through the center
column.

**Alternatives considered:** Keep odd-only generation; split the task into two
generators; opt out of even canonical profiles.

**Probe:** `self_check` accepts all five canonical inputs; default schedule and
semantic census cover both parities; the `off_by_one_axis` rival is refuted.

**Failure modes / limitations:** The schedule guarantees parity coverage only
for contiguous four-example windows. An external exporter that reorders or
subsamples examples should rerun lesson-level validation.

## 3. Allow a lawful odd-width center source

**Original rationale:** The old invariant required the center column to be
empty. The `8x7` canonical input has a nonzero center source, so that was an
incorrect simplification.

**Decision:** Permit center-column sources on odd widths. Schedule an explicit
centerline profile and isolate its center source in its row.

**Alternatives considered:** Accept center cells only in validation but never
generate them; duplicate the center value to an adjacent cell; treat it as a
special degenerate texture.

**Probe:** The canonical centerline input passes; the centerline witness fires
in all bands; the `duplicate_centerline` rival is checked and refuted.

**Failure modes / limitations:** Centerline frequency is scheduled rather than
caller-controlled by a separate axis, keeping the external axis surface small.

## 4. Use canonical-scale scheduled dimensions

**Original rationale:** The old random odd-width range produced zero exact
canonical profiles in 60 draws and only one draw inside the canonical envelope.

**Decision:** Schedule dimensions `6x8`, `8x7`, `7x10`, and alternating
`7x9`/`9x9`. Explicit overrides retain a broader `5..12` by `7..14` range.

**Alternatives considered:** Uniform sampling over the broad range; preserve
the old `half_w` parameter; maintain separate size schedules by difficulty.

**Probe:** Final profile gate is 60/60 exact and 60/60 envelope in all bands.
The override suite covers minimum and maximum dimensions.

**Failure modes / limitations:** Ordinary examples intentionally concentrate on
five dimensions. Broad-scale robustness relies on override-driven curricula.

## 5. Make source count the difficulty control

**Original rationale:** More source cells increase visual and bookkeeping load
without changing the core transformation. The old `cells` axis was not honest
across its declared range.

**Decision:** Use exact `n_cells` in `4..9`; default to 4 for easy, 6 for
medium/default, and 8 for hard.

**Alternatives considered:** Change grid size by difficulty; vary density labels;
allow 1-3 sources.

**Probe:** Boundary Cartesian tests verify every count with every dimension,
color count, and difficulty. `observe_overrides` returns the exact count.

**Failure modes / limitations:** Source count is only a rough difficulty proxy.
It does not independently control row collisions or object topology.

## 6. Require 2-4 realized source colors

**Original rationale:** Canonical inputs use four colors. The first replacement
allowed one color for broad Cartesian coverage, but the strict defect lint then
showed that generic one-color `short_line` and `solid_2x2` shapes passed the
validator.

**Decision:** Advertise `n_distinct_colors = 2..4`, default to four, and cycle
through the sampled palette so every requested color is actually present.

**Alternatives considered:** Keep one color and special-case the two linter
fixtures; require exactly four colors; treat color count as decorative.

**Probe:** A regression test first failed on the one-color impostors, then
passed after narrowing the grammar. The second strict defect lint has zero
findings. Exact two- and four-color boundaries pass the override matrix.

**Failure modes / limitations:** The generator no longer supplies monochrome
examples. That is intentional because they add little evidence for a
color-preserving mirror and admit weak shape priors.

## 7. Require two off-axis distances and blank destinations

**Original rationale:** A single mirror distance can leave the vertical axis
ambiguous, and prefilled destinations blur completion with conflict handling.
The canonical examples expose more than one distance and start targets blank.

**Decision:** Anchor one far-axis and one near-axis source. Reject inputs with
fewer than two off-axis distances or with a nonzero off-axis destination.

**Alternatives considered:** Pure random placement; permit already symmetric
inputs; allow occupied destinations and teach overlay conflict semantics.

**Probe:** The nearest-axis-only rival is refuted in every sampled draw. Identity
outputs and occupied-target structural impostors are rejected.

**Failure modes / limitations:** This is a teaching grammar narrower than the
full mathematical domain of the Racket program. It prioritizes visible,
unambiguous training examples.

## 8. Replace the decorative axis surface

**Original rationale:** Unknown. The imported generator declared `half_w`,
`palette_kind`, `cells`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture`, but several were inert,
redundant, or inconsistent with their declared ranges.

**Decision:** Expose only `grid_h`, `grid_w`, `n_cells`, and
`n_distinct_colors`. Consume all through `GenCtx`, reject unknown keys, and
provide exact observability.

**Alternatives considered:** Implement every legacy field; retain aliases for
backward compatibility; mark dead fields diagnostic.

**Probe:** Final override contract accepts 22,860/22,860 draws over 254 cases
and three bands, with no findings or warnings. Unknown-key verdict is
`rejected`.

**Failure modes / limitations:** Callers using undocumented legacy aliases must
migrate. This is preferable to silent no-op controls.

## 9. Guarantee branch coverage in each lesson

**Original rationale:** The old `EXAMPLES_NEEDED = 3` had no schedule and no
lesson semantics. Random odd-only examples could all support the same wrong
axis assumption.

**Decision:** Set `EXAMPLES_NEEDED = 4` and use a four-profile cycle independent
of seed. Every contiguous four-example window contains odd, even, and
centerline evidence.

**Alternatives considered:** Random branch choice; weighted sampling; retain
three demonstrations and hope all branches appear.

**Probe:** Sliding-window tests cover all starts and difficulty bands. The
semantic gate reports 12/12 identifiable lessons.

**Failure modes / limitations:** Noncontiguous lesson assembly can destroy the
guarantee. The exporter should validate the actual materialized window.

## 10. Encode plausible wrong rules as executable rivals

**Original rationale:** The baseline semantic stage was advisory `NO_CONTRACT`.
Comments and coarse distribution metrics could not tell whether examples taught
the selected transformation.

**Decision:** Implement seven named rivals, seven witnesses, explicit
witness-to-rival claims, and `lesson_identifiable`.

**Alternatives considered:** Rely on canonical acceptance only; use a single
identity check; document shortcuts without executable tests.

**Probe:** Final semantic gate reports 600/600 strict examples, 7/7 witnesses,
7/7 verified rival claims, and 12/12 identifiable lessons.

**Failure modes / limitations:** The list is not exhaustive. New shortcuts
should be added as rivals with a concrete generated witness.

## 11. Preserve failed iterations as evidence

**Original rationale:** The assignment asks for iteration rather than hiding
failed attempts.

**Decision:** Retain the first post-change strict run under
`checks/after_attempt1/`. It records the minimal-impostor failure that motivated
the 2-color minimum. Keep focused regression tests as a reusable future-agent
tool.

**Alternatives considered:** Overwrite failed evidence; weaken strict lint;
document the issue without a regression.

**Probe:** The first run fails specifically at `defect_lint`; the second run is
12/12 green; the focused suite is 8/8 green.

**Failure modes / limitations:** Check artifacts are larger than a prose-only
handoff, but they make the claimed improvement independently inspectable.
