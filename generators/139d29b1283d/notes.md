# 139d29b1283d — current design and review notes

Version 3.0.0, review `review-bc0c45d2cb547c41`. The selected Racket rule is
unchanged (`fcd41965ebef`). Generator SHA-256:
`d8916c811c9f894e620b29b9344d0eec388c084b31bddcf9e788ff3676217121`.

## Intended rule and input domain

Select the unique largest monochrome, four-connected color-3 component.
Normalize it using the minimum row and minimum column of its bounding box,
including when that corner is unoccupied. Translate the normalized shape to
the single color-1 anchor and the single color-2 anchor. On a new same-size
zero grid, paint only the in-bounds intersection in color 8. The input
template, distractors and anchors are not copied into the output. Labels
continue to come from Racket; Python alternatives are explicitly wrong rivals.

Inputs have 8..24 rows and columns, integer colors 0/1/2/3, one anchor of each
kind, a 2..8-cell largest template, and zero to two strictly smaller green
components. Booleans, missing anchors/templates, equal largest components,
ragged rows and unsupported colors are rejected. Clipped stamps must retain
a visible intersection; unclipped disjoint stamps legitimately produce zeros.
The validator accepts all three available canonical inputs.

## Decisions and reversals

- **R1, exact controls:** version 2.0.1 advertised but ignored template size,
  and its fallback silently substituted a fixed 14x14 scene. The new version
  honors `grid_h`, `grid_w`, `template_size`, `n_distractors` and `texture`
  together, in all bands, or fails explicitly after bounded construction.
  `None` means omitted; invalid types/ranges and unknown keys raise errors.
- **R2, honest domain:** the old all-zero 8x8 input passed validation, despite
  missing every required object. Validation now reports structural/type
  errors before scene analysis and enforces the domain above. `RULE_HASH`
  now binds the unchanged selected authority.
- **R3, teach the intersection:** canonical examples alone also fit seven
  wrong alternatives. Default raw indices use a period-three schedule:
  two all-rival witness slots, then one general slot. Witnesses use 5..8-cell
  templates, an empty bounding-box corner, genuinely nonrectangular overlap,
  and an earlier smaller green component. A completed grid must refute every
  declared rival. The general slot preserves smaller templates, canonical
  canvas profiles, no-overlap cases and clipped cases.
- **R4, reverse the initial distractor cap:** the first repair limited noise
  to three cells. Review found that this taught a size-four cutoff instead of
  largest-component selection. Strong slots now include an earlier distractor
  of at least four cells; all distractors remain smaller than the template,
  with other sizes spanning 1..template_size-1. The exact seven-versus-eight
  cell counterexample is retained below and checked against public Racket.
- Remove the old inert `palette_kind`, `palette_size`, `position_bias`,
  `n_distinct_colors` and `density` controls and palette-like texture aliases.
  They now raise unknown-axis or invalid-texture errors. Template color 3 and
  output color 8 are fixed; swapping anchor colors 1 and 2 preserves the
  intersection, but arbitrary warm/cool palette remapping does not.
  Valid textures are `overlap`, `no_overlap`, and `clipped`.

## Lesson contract and limits

Use three demonstrations and one query. Ordinary assembly preserves accepted
sample order; rotation checks hold out every labeled pair once and preserve
the order of the remaining three. Every four consecutive **raw** indices
contain at least two strong slots. This argument does not cover arbitrary
skipping of duplicate/rejected draws, and exact overrides can disable strong
slot prerequisites. Check materialized lessons and retain their accepted
indices rather than treating the schedule as a universal guarantee.

The final public Racket census materialized 100 lessons per easy/medium/hard
band: 300 lessons, 1,200 unique inputs, and 1,200 query rotations, with zero
declared-rival ambiguities or scoring/materialization errors. The declared
period census at seed 0 covers 3 starts x 3 bands: nine lessons, 36 rotations,
eight unique inputs, no ambiguity. These are finite results against seven
named rivals, not proof of unique inference or permission for training use.
Clipped generation currently puts an intersection cell at the bottom-right
corner; broader edge placement remains an explicit distribution limitation.

## Prior findings and regression evidence

The unresolved imported audit `review-3b145830caae97bf:v0001` described the
ignored size-eight request at seed 123/index 7, all-zero validator acceptance,
and missing rule hash on source `38e2ca6407cab0885019a5b8c7437e8d8e21a722a7cfeb5b239a171127259342`.
These three findings are repaired here. `tests/test_contract_repair.py`
replays the exact size request and malformed input; the current portable task
test stage passes 104/104 cases. The evidence registry remains unchanged
because this return's permitted patch scope excludes it; this is a
source-bound resolution proposal, not an approval or registry rewrite.

Minimal semantic examples are in `counterexamples/review-bc0c45d2cb547c41/`.
`workspace/semantic_probe.py` checks the actual declared rivals against all
canonical pairs and compares saved predictions with a public Racket receipt.
The return contains the full before/after reports, genuine failed iterations,
17 final Racket probes, and source-bound lesson censuses under `checks/`.

## Current scoped audit assessment

See `evidence/current-audit-assessment.json` for explicit source-bound dispositions. These are finite reviewer-reported checks; no owner rerun or universal qualification.
## Current reviewer considerations

Source SHA-256: `d8916c811c9f894e620b29b9344d0eec388c084b31bddcf9e788ff3676217121`.

# Decisions — review-bc0c45d2cb547c41

Repair target: `139d29b1283d`, version 2.0.1 -> 3.0.0. Final generator SHA-256:
`d8916c811c9f894e620b29b9344d0eec388c084b31bddcf9e788ff3676217121`.
The selected Racket authority `fcd41965ebef` and all canonical data are unchanged.

## R1: Exact controls and bounded construction

**Prior choice:** advertised sizes and canvas bounds were broader than the
generator honored. `template_size` was unused. Palette/density/position axes
were decorative, and special modes or exhausted placement returned a fixed
14x14 scene. The historic intent behind those unused axes is unknown; source
comments do not justify silently overriding user controls.

**New choice:** five pixel-observable controls: height and width 8..24,
template size 2..8, distractor count 0..2, and texture. All joint controls are
honored in easy, medium and hard. Numeric controls require actual integers,
excluding bool; `None` is equivalent to omission. Unsupported keys, invalid
types/ranges, and invalid difficulty/texture fail early. `observe_overrides`
recovers each value from the grid rather than echoing requested metadata.

Random connected shapes are bounded by the chosen canvas and retain room for
both stamps. After 80 random attempts, a small constructive hook family is
available for strong witnesses; the total is bounded at 96 attempts. This
backstop keeps the exact requested size/canvas/count/texture. Exhaustion raises
an explicit error. A silent control-changing fallback was rejected.

Evidence: the original battery's override stage failed, and the original
source failed 68 of the initial 90 focused cases. The final required battery
has no override findings and all 104 focused cases pass. The old exact
seed-123/index-7 size-eight request is a named regression. Initial malformed
test collection and oracle authoring errors are retained separately; they
are not counted as generator failures.

## R2: Domain, object semantics and fixed colors

Use monochrome four-connectivity, matching selected Racket `objects` behavior.
The common helper defaults differently, so its flags are explicit. Choose
the unique largest green component. Tied largest components are outside this
generator's declared domain, avoiding an accidental tie-order dependency.
Smaller components are legitimate distractors for largest-object selection.
Normalize minimum row and minimum column independently; the bounding-box
corner need not be an occupied template cell. Stamp origins are the anchors,
even if the normalized shape has an empty origin.

The output starts blank. Clipping applies to the translated stamp sets and
only their visible intersection is painted. No-overlap inputs are lawful and
produce zero grids; requiring every output to contain cyan was rejected.
Clipped cases must keep at least one visible intersection cell to avoid an
uninformative empty clipping branch. Input type/shape checks run before
component analysis, avoiding validator crashes on malformed cells.

Template color 3 and output color 8 are fixed symbols in the authority.
Anchor colors 1 and 2 may be swapped with each other because intersection
is commutative; they cannot be arbitrarily exchanged with background or the
template. The former warm/cool/varied controls were removed instead of
advertising unrestricted palettes. Legacy aliases now raise explicit errors;
this intentional API cleanup is reflected in the major version change.

## R3: Teach occupied-cell intersection rather than an accidental shortcut

All three usable canonical pairs have four-cell templates and no distractors.
Seven distinct wrong programs fit all three. Their names are:

1. `first_stamp_clipped_to_second_bbox`
2. `first_stamp_southeast_of_second_anchor`
3. `first_occupied_template_cell_origin`
4. `first_four_template_cells`
5. `first_color3_component`
6. `first_component_at_least_four`
7. `fill_overlap_bbox`

Each is registered in all three supported maps. That is seven hypotheses,
not 21 independent hypotheses. The reusable probe iterates the actual maps;
its list cannot silently drift away from generator declarations.

The original crop shortcut has a complete lesson-level failure, not merely a
contrived single grid: easy seed 6, medium seed 6, and hard seed 2 each have
three demonstrations at indices 0..2 that fit the shortcut, then a query at
index 3 that refutes it. All 12 original-source inputs were labeled through
public Racket. See `checks/semantic-investigation/baseline-lessons/verified.json`.
The broader original 300-lesson screening was Python geometry only; it is not
the final Racket census and is not represented as one.

**New distribution:** two default witness slots and one general slot per
three raw indices. A witness uses size 5..8, at least one earlier smaller
green object, an unoccupied normalized corner, and an overlap that differs
from its filled bounding box. Every completed witness is checked against
every declared rival. Fully random witness sampling without a lesson policy
was rejected because good examples can otherwise cluster outside a lesson's
demonstrations. Restricting the generator to a single fixed witness shape was
also rejected; random connected shapes precede the constructive backstop.

The general slot keeps template sizes 2..8, favoring canonical size four,
with no default distractors. Default modes there are weighted 3:1:1 for
overlap/no-overlap/clipped. Canonical canvas profiles 10x12, 11x13 and 12x14
are retained; witness slots also include the broader 8..24 canvas range.
The final profile diagnostic found 47/60 exact **canvas/color profiles**
(easy 16/20, medium 14/20, hard 17/20), versus 0/60 before. This is not a
claim that 47 samples reproduce canonical template shapes or entire grids.

## R4: Review changed the first repair

The first repair capped distractors at three cells. Independent review found
that "first component with at least four cells, otherwise largest" therefore
replaced largest-component selection. It fits canonical pairs too. A lawful
12x14 input with an earlier seven-cell bar and a later eight-cell bar makes
the rival miss cyan cell `(7,12)`; public Racket confirms the intended output.

We added the seventh rival and expanded distractor sizes. The first strong
distractor is 4..template_size-1 and appears before the main template in
row-major order. Other distractors span 1..template_size-1. The final placed
grid must still refute all rivals. New checks initially produced 13 failures
and one pass on the previous candidate, then all 104 tests passed after the
fix. See `checks/size-cutoff-before.log`, `checks/regression-after-cutoff.log`,
and the final `task_tests` report. Earlier six-rival passes are explicitly
intermediate evidence, not final acceptance evidence.

## Lesson assembly and measured scope

Default lessons contain **three demonstrations and one query** in accepted
sample order. Rotation checks hold out each of the four labeled pairs once,
preserving the remaining order. At least two strong slots occur in every
four consecutive raw indices; holding out one still leaves a full refuter.
The public materializer may advance over invalid or duplicate draws, so this
raw-index argument is not a proof under arbitrary rejection skipping. Exact
overrides may also disable the strong witness prerequisites.

Final Racket census: 100 lessons per band, deterministic hashed census seeds,
requested starts 0..99 in each band, 300 materialized lessons, 1,200 pairs and
1,200 unique inputs; all 1,200 holdouts pass the declared-rival test. The
period-three census additionally checks starts 0, 1 and 2 at seed 0 in each
band: nine overlapping lessons, 36 pair appearances, 36 holdouts, eight unique
inputs. Both reports retain actual accepted indices and source/rule identities.
The census tool's generic residue histogram uses modulus six; the schedule
contract and `schedule_coverage.period` are three. We report the declared
period separately to avoid conflating those fields.

All these results are finite. Undeclared rival rules, all random seeds and
all rejected-pair schedules remain unproved. Clipped placement currently
always includes the bottom-right output cell. This is a documented support
restriction, not a claim that every lawful clipping placement is sampled.
No training admission, approval status or external evidence registry changed.

## Scope and retained records

Only the selected generator, its current notes/summary, portable tests,
semantic probe and minimal counterexamples are patched. Both audit targets
remain byte-identical. Shared tooling findings are recommendations in
`FEEDBACK_TO_CODEX.md`, outside the task patch. The repository-wide test
command is recorded as blocked during collection by an absent original
packet file, separately from successful task gates.

Blind and post-repair solves remain separate. The post-repair attempt uses
the final generator bytes and declares prior exposure. The blind agent's
initial unimplemented stub check was incorrectly tagged `intent=solve`;
the immutable record is preserved and explicitly excluded from claims about
genuine failed inference. Both final programs match their visible examples;
masked query correctness remains unknown pending independent scoring.

## 2026-10-25 native parametric review

Built a task-local episode-fixed `finish=intersection_only|overlap_size_payload`
family under `workspace/parametric/` without changing the approved production
generator. The default program is the exact canonical Racket source. The relay
variant computes the visible intersection of the two translated largest-template
stamps, uses that input-derived cell count to choose the unique color-4 payload
of equal size, and paints both the intersection and payload color 8.

The family supports 2–6 demonstrations and four distinct matched-input queries,
including a substantive 30×30 boundary-spanning case. A finite audit covers both
settings, seeds 0/17/97, and demo counts 2/3/6; all six declared shortcuts are
rejected and 147 labels match protected Racket. Native qualification passes four
jobs and 40 protected-Racket evaluations. The retained wrong-intermediate witness
uses template size instead of visible-overlap size and changes the final output.
Status is reviewer-ready with exact-source owner acceptance pending; no training
admission is claimed.
