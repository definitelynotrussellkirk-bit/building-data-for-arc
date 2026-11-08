# Working notes: `b765f6c9ebeb`

## Review identity

- Assignment: `review-ca62fa1453076264`
- Canonical task: `b765f6c9ebeb`
- Canonical rule hash: `22554e067bcc`
- Baseline generator: version `2.2.1`
- Reviewed generator: version `3.0.0`
- Racket authority changed: **no**

Imported associated notes remain in `evidence/associated_notes.jsonl`; that file
was empty in this packet.

## Canonical rule understood

For every nonzero color independently, find maximal 4-connected components.
Erase components of size 1 and preserve components of size at least 2 exactly.
Background remains 0 and output shape equals input shape.

Two distinctions are essential:

1. differently colored cells that touch cardinally are still separate
   components;
2. same-colored cells that touch only diagonally are still separate components.

The old summary said “all components placed with cardinal separation,” which
removed the first distinction from generated data. Diagonal proximity was
allowed but not causally scheduled, which removed the second distinction from
measured lessons.

## Baseline findings

The required before-battery completed with 6 green, 1 advisory, and 5 failed
stages (`checks/before/checks/b765f6c9ebeb_before_battery_summary.json`).

### Source/contract defects

- `RULE_HASH` was missing.
- `position_bias` and `density` were single-token pseudo-axes and never probed.
- `texture` aliased `palette_kind`, so all four helpful texture values were dead.
- Negative fixtures (`no_singletons`, `no_objects`, `all_singletons`) were listed
  in the ordinary texture domain.
- Declared integer ranges were much wider than ordinary generation supported.
- `palette_size` and `n_distinct_colors` overlapped and became inert in many
  combinations.
- Unknown override keys were silently accepted.
- Exact component-count realization was not reported through
  `observe_overrides`.

The strict override checker recorded 9,889 findings and 2 warnings over 202,230
attempted draws (`checks/before/checks/b765f6c9ebeb_before_override_results.json`).

### Canonical-manifold defects

The old `self_check` rejected canonical train input 0 because a color-5
singleton touched a color-6 cell, and rejected canonical test input 0 because it
contained only one singleton. Only the presence of both rule branches is
semantically necessary. The old generator also achieved 0/60 exact or envelope
canonical-profile hits.

### Shortcut defect

A dedicated replay of the frozen generator measured 600 successful draws and 60
three-example lessons across easy/medium/hard. Both `multicolor_4` and
`same_color_8` matched the authority on 600/600 draws and survived all demos in
60/60 lessons. Identity matched 0/600. Evidence:
`checks/before_shortcut_probe.json`.

This establishes that the baseline's semantic ambiguity was real despite a
green diversity stage.

## Design decisions implemented

### Honest ordinary axes

The ordinary axis contract is now exactly:

- `grid_h`: 5..8
- `grid_w`: 5..10
- `singletons`: 2..3
- `objects`: 2..3
- `palette_kind`: `default|warm|cool|varied`
- `texture`: `color_touch|diagonal_same_color|separated`

Unknown keys fail immediately. `observe_overrides` recovers exact singleton and
survivor counts from the grid.

### Default profile schedule

The six profile cycle is:

1. 5x6, 2 singletons, 3 survivors, default palette;
2. 5x5, 2 singletons, 3 survivors, warm palette;
3. 5x7, 2 singletons, 3 survivors, cool palette;
4. 6x8, 3 singletons, 2 survivors, varied palette;
5. 7x9, 3 singletons, 3 survivors, warm palette;
6. 8x10, 3 singletons, 3 survivors, cool palette.

The first three yield exact canonical `(h,w,palette-size)` profiles
`(5,6,6)`, `(5,5,5)`, `(5,7,5)`. The later profiles exercise all declared
integer boundaries and preserve broader geometric coverage.

### Semantic textures

- `color_touch`: construct a survivor and a differently colored adjacent
  singleton before filling the scene. This refutes color-blind 4-connectivity.
- `diagonal_same_color`: construct two same-colored singleton cells touching
  only diagonally. This refutes same-color 8-connectivity.
- `separated`: maintain external cardinal separation for a plain example.

The texture schedule uses `sample_index % 3`; every ordinary three-example
window therefore includes the two decisive motifs, and `lesson_identifiable`
checks the actual demos rather than assuming the schedule worked.

### Shapes and placement

Surviving components use a deterministic bank of connected polyominoes of size
2–5. Difficulty caps maximum size (easy 3, medium 4, hard 5), with additional
small-board caps. Decisive motifs are placed first. Remaining components are
placed under same-color noncontact constraints; mixed-color contact is allowed
except in `separated` texture. Exact component counts and required witnesses are
re-observed before return. Generation retries at most 120 layouts and then fails
loudly with the request details.

### Negative fixtures

`no_singletons`, `no_objects`, and `all_singletons` remain deterministic
fixtures for negative/mutation testing. They are intentionally not in the
ordinary texture domain and cannot be combined with ordinary overrides.

### Semantic diagnostics

Added:

- `rule_mirror`
- rivals `identity`, `multicolor_4`, `same_color_8`
- witnesses `keep_and_erase`, `mixed_color_contact`,
  `same_color_diagonal_singletons`
- `WITNESS_RIVALS`
- `strict_canonical_like`
- `lesson_identifiable`
- `schedule_profile`

The Python mirror supports fast diagnostics only. Canonical Racket remains the
authority and is checked by rule smoke/authority synchronization.

## Test-first chronology

1. Saved the frozen 2.2.1 implementation in
   `workspace/generator.before-2.2.1.py`.
2. Added six focused regressions before replacement; result was 5 failed,
   1 passed (`checks/tests-red.log`).
3. Implemented 3.0.0; focused tests became 6 passed.
4. First full after-battery stopped at lint because local variable `obj_cells`
   exactly matched a reserved Racket primitive identifier
   (`checks/after-attempt1/checks/b765f6c9ebeb_after_lint.log`).
5. Added a source-AST regression, observed it fail
   (`checks/lint-name-red.log`), renamed the variable to `survivor_cells`, and
   reached 7 passed (`checks/target_pytest.log`).
6. Reran the complete battery to 12/12 green.

## Verification evidence

### Reusable distribution probe

`workspace/distribution_probe.py` checks:

- the full declared boundary/category matrix;
- exact override observability;
- deterministic replay and process-global RNG purity;
- texture witness realization;
- both rule branches;
- sliding three-demo lesson windows;
- canonical profile schedule.

Result (`checks/b765f6c9ebeb_distribution_probe.json`):

- 768/768 override cases generated;
- 216/216 lesson windows identifiable;
- 768/768 keep-and-erase witnesses;
- 256/256 requested mixed-color-contact witnesses;
- 256/256 requested diagonal-singleton witnesses;
- no failures.

Rerun from packet root:

```bash
PYTHONPATH=repo/shared/runtime python3 \
  repo/generators/b765f6c9ebeb/workspace/distribution_probe.py \
  --json-out checks/b765f6c9ebeb_distribution_probe.json
```

### Required after-battery

`checks/after/checks/b765f6c9ebeb_after_battery_summary.json` reports 12 green,
0 advisory, 0 failed, 0 interrupted, 0 pending.

Notable measured values:

- 600/600 strict canonical-like draws;
- all 3 canonical inputs accepted;
- witness profile coverage in every difficulty band;
- each rival claim held on 60 checked fired examples;
- 12/12 lessons identifiable;
- 26/60 exact canonical-profile hits;
- 300 diversity pairs, 100% unique inputs/outputs;
- 18,180/18,180 strict override draws accepted over 202 cases;
- zero override findings/warnings;
- Racket authority synchronization pass.

### Additional suite

Python repository tests: 138 passed, 28 skipped
(`checks/repo_pytest_python.log`). The skipped tests depend on direct Racket
integration; the task's required Racket stages completed in the all-green
battery. An optional whole-repository Racket pytest attempt exceeded the
external execution wrapper's wall-clock cap and is not claimed as completed.

## Fresh solve

After generator work, I followed the visible-only solve protocol. I had earlier
rule exposure and declared `yes`; I did not consult a reference during the solve.
One Python revision passed all 3 visible examples. The masked query label was
withheld as designed. See `solve/SOLVE_NOTES.md`,
`solve/attempts/0001/report.json`, and `solve/summary.json`.

## Remaining limitations and future checks

- The bounded constructive search is empirically robust over the declared
  matrix, not formally proven for every seed.
- The three rivals are the highest-value obvious shortcuts, not an exhaustive
  hypothesis class.
- Any future change to bounds, palette families, shapes, or contact policy must
  rerun both the strict override battery and `distribution_probe.py`.
- Any future change to `EXAMPLES_NEEDED` or texture scheduling must rerun sliding
  lesson-window checks, not only per-draw witness counts.
- Preserve the exact rule hash and rerun authority sync before any source cleanup.
## Current reviewer considerations

Source SHA-256: `a86c084fe0dbb32c9c98af62025a7a19016f1292e2a6a511b7946dad47fc8709`.

# Design decisions for `b765f6c9ebeb`

## 1. Treat color as part of component identity

**Choice.** A component is a maximal nonzero set connected cardinally **and
sharing one color**.

**Why.** The canonical authority preserves/erases same-color components. A
canonical input contains a singleton touching a differently colored survivor;
the old `self_check` rejected it because it imposed color-blind separation. The
baseline failure is recorded in
`checks/before/checks/b765f6c9ebeb_before_selfcheck.log`.

**Alternative rejected.** Keeping every nonzero 4-connected island as one
object. That is contradicted by the canonical example and is explicitly modeled
as the `multicolor_4` rival.

**Failure mode guarded.** A model can otherwise learn “erase isolated nonzero
pixels” instead of “erase singleton same-color components.”

## 2. Use 4-connectivity, not 8-connectivity

**Choice.** Diagonal contact does not merge same-color cells.

**Why.** The canonical examples contain diagonal same-color singleton behavior,
and the rule authority uses cardinal connectivity. The `diagonal_same_color`
texture deterministically places two same-color singleton cells touching only at
a corner.

**Alternative rejected.** Randomly allowing diagonal proximity and hoping it
occasionally creates a useful counterexample. The frozen generator did that only
implicitly, and both the 4- and 8-connected rivals matched all 600 measured old
draws and all 60 sampled old lessons (`checks/before_shortcut_probe.json`).

**Failure mode guarded.** An 8-connected shortcut can fit every training example
while producing the wrong answer on diagonal contacts.

## 3. Require both rule branches in every ordinary draw

**Choice.** Ordinary generated inputs contain at least one singleton and at
least one multi-cell component. Exact defaults/overrides are 2–3 of each.

**Why.** Every example should demonstrate both erasure and preservation. Counts
of 2–3 provide multiple objects without making 5x5 canonical-profile grids
fragile to place. The reusable boundary census successfully realized every
combination of 2/3 singletons and 2/3 surviving objects over all declared
heights, widths, palettes, textures, and difficulties.

**Original rationale.** The old file also aimed for mixed singleton and
multi-cell scenes, but its comments were the only rationale available. It
advertised much wider count ranges than it could reliably or ordinarily sample.

**Alternatives rejected.** One component of either class gives weak examples;
allowing zero of either class in ordinary draws creates lessons where the rule's
other branch is unobservable. Those cases remain explicit negative fixtures,
not training textures.

## 4. Separate ordinary textures from negative fixtures

**Choice.** Ordinary `texture` values are only:

- `color_touch` — differently colored singleton touches a survivor;
- `diagonal_same_color` — two same-color diagonal singletons;
- `separated` — uncomplicated components with no cardinal contact.

`no_singletons`, `no_objects`, and `all_singletons` remain deterministic
fixtures handled before ordinary axis drawing, but are not listed in the
ordinary `AXES['texture']` domain.

**Why.** The old metadata mixed invalid-for-training fixtures into the ordinary
texture domain, causing a defect-lint failure and many incompatible override
cases. Ordinary textures now describe positive semantic coverage, while
negative fixtures remain useful for mutation/testing.

**Alternative rejected.** Declaring all six values together and documenting
incompatibilities. That would preserve a misleading ordinary axis and inflate
the override matrix with cases that intentionally violate the task's training
invariants.

## 5. Rotate semantic textures deterministically by sample index

**Choice.** `schedule_profile()` cycles
`color_touch → diagonal_same_color → separated` using `sample_index % 3`.

**Why.** `EXAMPLES_NEEDED = 3`, so every contiguous aligned three-example lesson
contains both shortcut-refuting cases and a plain case. `lesson_identifiable`
checks the demos directly rather than trusting the schedule. The stress probe
also checked 216 sliding windows, including unaligned starts, and all were
identifiable.

**Alternative rejected.** Independent random texture draws. Even balanced
marginals can create an individual lesson with no decisive witness; training
quality is lesson-level, not only corpus-level.

**Failure mode guarded.** A rival may be refuted somewhere in a large corpus yet
survive all demonstrations presented with a particular query.

## 6. Match canonical profiles first, then broaden conservatively

**Choice.** The six default profiles begin with:

1. `5x6`, default palette, 2 singletons, 3 survivors;
2. `5x5`, warm palette, 2 singletons, 3 survivors;
3. `5x7`, cool palette, 2 singletons, 3 survivors.

Those produce palette sizes 6, 5, and 5 respectively, exactly matching the
three canonical `(height, width, palette-size)` profiles. Profiles 4–6 expand to
`6x8`, `7x9`, and `8x10`, exercise 3-singleton/2-or-3-object counts, and include
the varied palette.

**Why.** The old defaults were 6–9 by 7–10 and had 0/60 canonical-profile
support. Canonical anchoring reduces distribution shift, while the later
profiles retain useful geometric diversity and hit every declared numerical
boundary in ordinary generation.

**Original rationale.** No evidence tied the old 6–9/7–10 bounds to this task;
they appear to have been generic sparse-grid defaults. Therefore I treated that
rationale as unknown rather than authoritative.

**Alternatives rejected.** Generating only the three canonical shapes would
unnecessarily narrow the corpus. Preserving the old larger-only sizes would
continue the measured profile failure.

## 7. Declare only ranges the generator actually supports

**Choice.** `grid_h` is 5–8 and `grid_w` is 5–10; exact component counts are 2–3.
The generator rejects values outside these ranges through `GenCtx`.

**Why.** The prior contract declared 4–16, 1–10, and 1–8 while ordinary draws
used much smaller subranges. A contract should describe tested capability, not a
hypothetical future range. The final strict override gate covered all declared
values and reported zero findings.

**Alternative rejected.** Expanding the constructor to all old advertised
bounds merely to preserve metadata. Small boards with many components and large
boards with few components would either be uninformative or require a more
complex compatibility contract without improving this task's lessons.

## 8. Keep four palette families, remove duplicate palette axes

**Choice.** Retain `palette_kind = default|warm|cool|varied`; remove
`palette_size` and `n_distinct_colors` as independent controls.

**Why.** In the old implementation, those controls overlapped and became inert
under many combinations. A palette family is a meaningful generative choice;
actual distinct colors may repeat across components and should not be promised
as a second exact axis unless it is independently constructed and observed.

The current palettes all contain enough colors to realize the required motifs.
`diagonal_same_color` deliberately reuses one color for the paired singleton
components; other assignments may repeat as needed without changing component
semantics.

**Alternatives rejected.** Keeping both numerical palette axes and declaring
complex interactions. The strict gate showed that the old combination produced
many inert-axis findings. The simpler contract is easier to falsify and teaches
the same rule.

## 9. Use connected shape banks with difficulty-limited maximum size

**Choice.** Surviving components are drawn from a fixed bank of connected
polyominoes of size 2–5. Easy caps at 3, medium at 4, hard at 5; small boards
receive additional caps.

**Why.** The task depends on component cardinality, not a particular rectangle
or domino template. Shape variety prevents template memorization, while size
caps preserve constructive reliability on canonical 5-row boards.

**Original rationale.** Version 2.2.1 had already expanded beyond four fixed
shapes to random polyominoes. I kept that useful intent but made the supported
shape bank and caps explicit and deterministic.

**Alternative rejected.** Fully random walks/polyomino growth. That makes exact
placement and replay harder to diagnose without adding a semantic dimension.

## 10. Construct decisive motifs first, then fill the remainder

**Choice.** For `color_touch`, place a domino survivor and adjacent
other-colored singleton first. For `diagonal_same_color`, place the diagonal
pair first. Then place remaining objects/singletons with constraints appropriate
to the texture.

**Why.** Retrofitting a witness after random placement often fails or silently
changes component counts. Motif-first construction makes the causal feature
explicit. Final generation re-observes exact counts and rechecks the witness
before returning.

**Alternative rejected.** Generate a generic scene and search for incidental
witnesses. That can bias acceptance/rejection unpredictably and offers no
coverage guarantee.

## 11. Permit mixed-color contact only when it is useful

**Choice.** `color_touch` and `diagonal_same_color` allow cardinal contact
between differently colored components, while `separated` forbids all external
cardinal contact. Same-color external contact is always forbidden because it
would merge components.

**Why.** The canonical manifold allows mixed-color contact. Including both
contact and fully separated scenes prevents either relation from becoming an
accidental invariant.

**Failure mode guarded.** Always-separated data enables the color-blind
component shortcut; always-touching data could create a different texture leak.

## 12. Make overrides exactly observable and reject unknown keys

**Choice.** `observe_overrides(grid)` reports realized singleton and survivor
component counts. Grid dimensions are directly observable; palette and texture
are categorical construction controls. Unknown keys raise `ValueError`.

**Why.** The old generator silently accepted misspelled/renamed keys and did not
report exact component-count realization. That made a nominally accepted
training request impossible to audit. The final override gate accepted
18,180/18,180 requested draws, found no mismatch, and confirmed unknown-key
rejection.

**Alternative rejected.** Silently ignoring unsupported controls for backward
compatibility. This converts caller mistakes into mislabeled data.

## 13. Add a Python mirror only for diagnostics, not as authority

**Choice.** `rule_mirror()` implements the simple same-color 4-connected rule in
Python for focused tests, witnesses, and lesson checks. The canonical Racket
program remains the authoritative target and was not edited.

**Why.** Reusable semantic probes need a cheap oracle for thousands of local
comparisons, but source authority must remain singular. Required Racket
rule-smoke and authority-sync stages provide cross-language verification.

**Alternative rejected.** Rewriting or “cleaning up” the Racket source. There was
no semantic defect in the authority, and changing it would expand scope without
benefit.

## 14. Declare explicit rivals and verify lesson identifiability

**Choice.** Three rivals are executable: identity, color-blind 4-connectivity,
and same-color 8-connectivity. Witness-to-rival claims are declared, and
`lesson_identifiable` independently checks each demonstration set.

**Why.** Corpus diversity metrics do not answer whether a plausible wrong rule
fits all demonstrations. The old generator had 100% survival for the two
connectivity rivals in the measured probe; the repaired semantic gate verified
all three rival claims and 12/12 lessons.

**Alternative rejected.** Relying on `self_check` alone. `self_check` validates a
single input's manifold; it cannot prove that a set of demonstrations identifies
the transformation.

## 15. Bounded retry policy

**Choice.** Try up to 120 constructive layouts, then fail loudly with the exact
requested dimensions, counts, and texture.

**Why.** This avoids unbounded search while retaining deterministic replay.
Exact post-construction observation prevents a near miss from being returned as
success.

**Known limitation.** Passing the complete declared boundary census does not
mathematically prove every seed will place successfully. The explicit failure is
preferable to clamping or silently changing requested axes.

## 16. Reusable verification artifact

**Choice.** Keep `workspace/distribution_probe.py` with a single rerunnable
command and JSON output.

**Why.** Future changes to shape banks, bounds, or placement can otherwise pass a
small unit suite while breaking a rare override combination or a shifted lesson
window. The probe covers 768 cross-product cases and 216 lesson windows and
reports replay tuples for failures.

**Limitations.** It is a deterministic census of declared boundaries and
categories, not randomized fuzzing or a proof over all seeds. It complements,
rather than replaces, the repository battery.

## 2026-10-25 native parametric review — erase then bridge

**Choice.** Keep `finish_rule=erase_only` as the exact canonical Racket bytes and
add `finish_rule=erase_then_bridge`. Stage A removes same-color 4-connected
singletons. Stage B consumes that cleaned grid, finds row/column spans containing
at least four cells of one surviving color with only zeroes between their
endpoints, and fills the intervening zeroes.

**Teaching construction.** Every scene contains a raw-ready span plus a second
span blocked by a singleton. Thus bridge-before-erase fills only the first span,
while the selected order fills both. The first two demonstrations separately
teach horizontal color 7 and vertical color 8. They reject identity, raw-only or
wrong-order bridging, row-only, column-only, size-at-least-three, fixed-color-7,
and color-blind shortcuts. Inputs are matched across settings, 2–6 demonstration
prefixes are stable, and four queries are stored for sequential reveal. The
fourth query is 30x30, touches all boundaries, has at least 120 occupied cells,
and contains both bridge orientations, at least six singleton distractors, and
at least six surviving components.

**Evidence.** Twenty-one focused tests passed, including twelve protected-Racket
labels. The 12-seed audit covered 72 episodes at demo counts 2, 3, and 6; all
eight rivals were rejected by the visible demonstrations and 276 pair checks
confirmed the wrong-order output differs. Native qualification passed both
settings at seeds 0 and 17 (four jobs, 32 protected-Racket evaluations). The
protected wrong-order witness changes eight cells on a qualified 13x15 query.

**Portability repair.** The pre-existing task test now uses
`find_root`, `canonical_path`, and `load_selected_generator` instead of a fixed
parent depth and manual source import. The portable task suite passes 28/28.

**Limit.** The rival census is finite and does not prove uniqueness against
arbitrary programs. This is reviewer-ready source, not owner-accepted or
training-admitted.
