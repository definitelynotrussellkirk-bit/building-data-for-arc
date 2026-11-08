# Working notes: 1a58c96bb078

## Intended rule and authority

Row 0 is a per-column legend. For each body cell equal to cyan (`8`), replace it
with the nonzero value at row 0 of the same column. If that header is zero, keep
the cyan cell. Preserve every non-cyan cell unchanged. The selected canonical
Racket authority was not edited; `RULE_HASH = "341c4a414d7c"` pins it.

Current generator: version `2.0.0`, SHA-256
`19aefdb0d934a8981c522178e747668a9a66832cf927c62f0c5c18620a70c075`.

## Reversed baseline decision

The imported `1.2.1` sampler put cyan markers only in legend columns and emitted
no unrelated nonzero body content. It also advertised single-valued
`position_bias` and `marker_density` axes and several out-of-grammar degenerate
textures. The retained audit `review-f89bda355e4fdac7:v0001` was used as the
lead: against source SHA-256
`3d8657b314646298e1c6301cc1ad804b3389b38376e46eb76dbdadad39faf6d4`,
0/900 sampled inputs contained a nonzero non-cyan body cell, so a destructive
"blank the body, then paint mapped markers" rival survived all sampled support.

The new choice is to make preservation observable in every generated input and
to schedule unmapped cyan cells. This directly targets the rule's two unchanged
branches instead of retaining decorative or non-probeable metadata.

## Current distribution

Every lawful generated input has:

- a 7..14 by 7..16 grid;
- 1..5 distinct nonzero, non-cyan legend colors in row 0;
- the same exact 1..4 cyan markers in each legend column;
- 1..4 cells of one non-legend color below empty headers, all preserved; and
- 0..3 cyan cells below empty headers, also preserved.

The exact observable controls are `grid_h`, `grid_w`, `n_legend_cols`,
`markers_per_col`, `n_preserved`, `n_inert_eights`, and `distractor_color`.
Unknown keys and non-integral integer overrides fail loudly. Every fourth draw is
a canonical-scale anchor cycling through 7x7, 8x8, and 9x9 profiles. The other
three residues schedule one, two, and three unmapped cyan cells. Thus any four
consecutive generated pairs, with any one held out as query, leave three
demonstrations that still contain preservation evidence and at least one
unmapped-cyan witness.

## Semantic contract

`rule_mirror` is a diagnostic Python mirror only; Racket remains label
authority. Two executable rivals are retained:

1. `clear_body_then_paint` erases unrelated body cells; every generated input
   refutes it and the canonical pairs already refute it.
2. `drop_unmapped_eights` applies mapped recoloring but erases cyan below empty
   headers; it fits all canonical pairs, so the scheduled generated witness is
   required.

`lesson_identifiable` requires three demonstrations and verifies that both
rivals are refuted. The minimal current witnesses, including inputs and rival
outputs, are in
`counterexamples/preservation-shortcuts-v2.json`. Focused regression coverage is
in `tests/test_generator.py`.

## Verification evidence

- Baseline checkpoint: `WORK/checks/before/` retained a lint failure for missing
  `RULE_HASH` and two non-probeable axes; self-check and rule smoke were green,
  while the interrupted aggregate remained incomplete.
- Final battery: `WORK/checks/after/checks/1a58c96bb078_after_battery_summary.json`
  reports 12/12 stages green.
- Focused tests: 31/31 pass in `WORK/checks/task-tests/` (and the earlier TDD red
  run is retained in `WORK/checks/task-tests-red/`).
- Semantic smoke: 600/600 strict generated inputs, 3/3 canonical inputs accepted,
  both rival claims verified, 12/12 ordered lessons identifiable, and 0/48
  ambiguous held-out rotations.
- Large census: `WORK/checks/lesson-census.json` reports 300/300 ordered lessons
  and 1,200/1,200 rotations with zero ambiguity or errors, using 1,200 unique
  inputs.
- Exact override gate: 73,800/73,800 accepted draws across 820 cases and three
  bands, with zero findings.

## Assumptions and limits

The teaching grammar is intentionally narrower than the full rule: it requires
exactly one preserved body color, equal marker counts in legend columns, and the
stated size/count ranges. Those restrictions make all advertised axes observable
and keep canonical examples inside the strict manifold, but they do not describe
every lawful grid the Racket rule could transform. The finite rival set and
sampled lesson census do not prove unique induction against all imaginable
rules. Palette identities and spatial placements remain randomized, but the
four-residue teaching schedule is deliberate rather than i.i.d. The repair
changes no Racket source and makes no training-approval claim.

## Open findings

No blocking task-local finding remains in this review. A future maintainer may
choose to broaden preserved body colors or marker-count asymmetry after adding
new observables and witnesses; doing so is not required for the current rule or
for the measured lesson policy.
## Current reviewer considerations

Source SHA-256: `19aefdb0d934a8981c522178e747668a9a66832cf927c62f0c5c18620a70c075`.

# Decisions: 1a58c96bb078

## 1. Preserve the Racket authority

**Decision.** Keep the canonical Racket rule unchanged and pin
`RULE_HASH = "341c4a414d7c"` in the Python generator.

**Why.** The canonical rule and examples already express the intended behavior:
row 0 is a column legend; cyan body cells are recolored only when their column
has a nonzero header; unmapped cyan and all non-cyan cells are preserved. The
observed defect was missing generator support, not an incorrect authority.

**Alternatives rejected.** Changing the rule to clear unrelated body cells would
make the old generated distribution self-consistent, but would contradict the
canonical example containing a preserved color-6 body cell. Broadening or
rewriting the Racket implementation offered no value and would add authority
risk.

**Probe.** Rule smoke and authority synchronization are green in
`checks/after/`; the final solve episode is bound to generator SHA-256
`19aefdb0d934a8981c522178e747668a9a66832cf927c62f0c5c18620a70c075` and
rule hash `341c4a414d7c`.

## 2. Replace decorative axes with exact observable controls

**Prior choice.** Version `1.2.1` advertised `position_bias=top_row` and
`marker_density=mixed`, each with only one enum token. The linter could not
probe either axis. Several declared degenerate textures were also outside the
useful teaching grammar.

**New choice.** Expose seven controls that can be recovered exactly from pixels:
`grid_h`, `grid_w`, `n_legend_cols`, `markers_per_col`, `n_preserved`,
`n_inert_eights`, and `distractor_color`.

**Why.** Exact controls make distribution claims testable and eliminate metadata
that varies only in name. They also target the semantics that were missing:
preserved content and unmapped cyan.

**Validation.** Unknown keys and wrong types fail before generation. The source-
bound override matrix exercised 820 cases in three bands with 30 seeds each:
73,800/73,800 accepted draws, zero findings and zero warnings.

**Alternatives rejected.** Keeping the old axes as diagnostic fields would
silence part of the lint signal without improving data. Adding many shape or
palette controls would increase combinatorics without addressing a demonstrated
failure.

## 3. Put preserved foreign content in every sample

**Decision.** Generate 1–4 cells of one non-legend, non-cyan color below empty
header columns in every sample.

**Why.** The old sampler had 0 such cells in 900 audited draws, allowing a model
to learn “blank the body, then repaint mapped markers.” A universal per-sample
witness is cheap and directly separates that rival from the intended rule.

**Placement constraints.** Preserved cells stay below empty headers so they do
not collide with mapped marker columns. Their color differs from all legend
colors so the observation is unambiguous.

**Alternatives rejected.** Making preservation rare would leave many lessons
shortcut-compatible. Allowing arbitrary multiple body colors now would widen
the grammar without adding a new semantic branch; it can be revisited after
adding explicit controls and coverage.

**Failure mode considered.** A fixed body location or color could itself become
a shortcut. Both are randomized, while only the presence/count is controlled.

## 4. Schedule unmapped cyan instead of sampling it independently

**Decision.** Use sample-index residues modulo four to emit 0, 1, 2, and 3 cyan
cells below empty headers. Residue zero is a canonical-scale anchor; residues
one through three carry increasingly explicit unmapped-cyan evidence.

**Why.** The shortcut `drop_unmapped_eights` fits all three canonical pairs, so
canonical support alone cannot refute it. Independent low-probability sampling
could produce a three-demo lesson with no counterexample. A short deterministic
schedule makes teaching support auditable.

**Guarantee.** Any four consecutive generated pairs, with any one held out as
query, leave three demonstrations containing foreign-content preservation and
at least one unmapped-cyan witness. The focused test checks 12 consecutive
starts and all four held-out positions. The larger census checked 300 production
lessons and 1,200 rotations with no surviving declared rival.

**Alternatives rejected.** Putting unmapped cyan in every sample would remove a
useful canonical-like anchor and reduce variation. Pure random sampling would
not guarantee lesson-level evidence. A longer schedule was unnecessary for the
two known preservation branches.

**Limit.** The shared production scheduler reports a six-residue start plan;
the generator's semantic profile itself is four-residue. The retained census
samples both the production plan and every held-out position but does not prove
all hypothetical external assemblers safe.

## 5. Retain canonical-scale anchors

**Decision.** Every fourth draw cycles among 7×7, 8×8, and 9×9 anchors with
canonical-compatible counts.

**Why.** The repair should broaden semantic support without drifting entirely
away from canonical geometry. The profile-floor gate requires real support in
each difficulty band, not just acceptance of imported examples.

**Measured result.** Across 60 profile-floor draws there were 18 exact hits and
22 envelope hits, with at least one exact hit in easy, medium, and hard.

**Alternative rejected.** Difficulty-disjoint dimension ranges were rejected
because exact canonical controls then failed in some bands and made overrides
context-dependent.

## 6. Use executable rivals and witnesses

**Decision.** Keep two pure deterministic rivals:

- `clear_body_then_paint`: copy row 0, erase body content, recolor only mapped
  cyan markers.
- `drop_unmapped_eights`: apply mapped recoloring, but replace unmapped cyan by
  background.

Pair them with `preserved_foreign_body` and
`inert_eight_outside_legend` witnesses, and require three-demo lessons to refute
both.

**Why.** Prose warnings do not test training data. Executable rivals let the
semantic gate and census measure whether demonstrations distinguish intended
behavior from plausible shortcuts.

**Canonical handling.** Only `drop_unmapped_eights` is listed as a
canonical-fitting shortcut because `clear_body_then_paint` is already refuted by
a canonical preserved cell. Both remain lesson competitors because generated
support must continue to teach both branches.

**Limit.** No finite rival set proves unique induction. Results should be read as
“no ambiguity found against declared rivals,” not universal proof.

## 7. Keep a strict teaching grammar narrower than the full rule

**Decision.** `self_check` and `strict_canonical_like` require one preserved body
color, equal mapped-marker counts per active legend column, 1–5 distinct legend
colors, and bounded counts/dimensions.

**Why.** A narrow grammar makes every axis observable, preserves all canonical
pairs, supports deterministic lesson scheduling, and avoids accidental overlap
between witnesses.

**Alternatives rejected.** Treating every mathematically transformable grid as
strict would make counts and role extraction ambiguous. Expanding to asymmetric
marker counts or multiple preserved colors is reasonable future work, but needs
new axes, probes, and counterexamples rather than an undocumented broadening.

## 8. Test first and retain failures

The new task tests were run against the original source before implementation.
That red run produced 28 failures and 3 passes, proving the tests covered missing
behavior rather than merely restating the final code. The same 31 tests then
passed against the repaired source. The incomplete baseline battery, red tests,
full green battery, large census, and audit reproductions are all retained.

The initial complete-battery wrapper outlived the first command window. I did
not count that as a pass; I inspected its checkpoint, kept the incomplete
`before` evidence, then ran a separate completed source-bound `after` battery.
