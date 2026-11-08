# Working notes: 1cbcf1ed9a32

## 2026-10-11 review — assignment `review-bf076c469feaf7ca`

### Intended rule and authority

Two full-height color-5 dividers create three equal-width panels. For each
panel, take the unique largest monochrome 4-connected object and reduce its
coordinate set to the lexicographically smallest member of its D4 orbit.
Exactly one canonical signature occurs twice; render that normalized shape in
color 8. The synchronized Racket program remains authoritative and unchanged.
The generator now pins it with `RULE_HASH = dc0d41aa47ba`.

### Reproduced baseline defects

Version `1.4.0` always gave the distractor a different number of cells from the
common pair. Consequently, the hybrid shortcut “choose a shape from the unique
repeated cell count, otherwise choose panel 0” matched every ordinary v1.4 draw
and all three canonical labels. The source also advertised stale or inert axes,
accepted unknown keys and weak scalar types, rejected declared values in some
difficulty bands, exposed malformed cases as ordinary textures, lacked an
executable semantic contract, and omitted the canonical rule pin. The before
battery recorded 7 green, 2 advisory, and 3 failed stages (`lint`,
`defect_lint`, and `override`) for source
`431479ffc49e73f578d991b4179bc1bc3e906966d6f3225e680d6dba3b0fc0c8`.

### Selected repair

Version `2.0.0` makes all three largest objects share one exact cell count while
requiring exactly two D4 matches. It enumerates every free polyomino class of
3–7 cells and filters by the selected panel envelope. The public override
surface is reduced to six exact, observable controls:

- `grid_h=5..8`
- `panel_w=4..7`
- `common_cells=3..7`
- `common_pair=0,1|0,2|1,2`
- `palette_kind=default|warm|cool|varied`
- `secondary_objects=none|singletons`

Unknown keys, booleans masquerading as integers, invalid enum values, negative
sample indices, and unknown difficulties reject explicitly. Optional singleton
components are separated from the main object by a guaranteed blank row and do
not change the unique-largest-object rule.

### Teaching schedule and executable rivals

A four-slot schedule supplies one canonical-size anchor and three expanded
profiles. Two slots make panel 0 the distractor, and all four common-pair
placements needed by the lesson are represented. `EXAMPLES_NEEDED = 4` and
`LESSON_SCHEDULE_PERIOD = 4` are declared.

The semantic contract includes two canonical-fitting rivals:

- `first_panel`
- `repeated_cell_count_else_first_panel`

The `panel_zero_distractor` witness refutes both. Every cyclic start of the
four-slot schedule was materialized at seed 0 in all three bands, and all five
query positions were checked: 12/12 lessons and 60/60 rotations were
identifiable. A broader production census materialized 300 lessons (100 per
band), 1,500 pairs and 1,500 query rotations with 1,500 unique inputs and zero
ambiguities, hook warnings, materialization errors, or scoring errors.

### Retained counterexample

`counterexamples/repeated_cell_count_else_first_panel.json` is source-bound to
final generator SHA-256
`4c969fc26956568436a826318dacab429db49f3aa709881a142ee8232bd1da6e`.
All three largest objects contain four cells, panels 1 and 2 share the intended
D4 class, and panel 0 is the distractor. The intended output is
`[[8,8,8],[8,0,0]]`; the old shortcut returns
`[[8,8,0],[0,8,8]]`.

### Measured final state

- task-local regression suite: 50/50 passing;
- exact override matrix: 20,160/20,160 accepted draws over 224 cases and all
  three bands, with zero findings or warnings and unknown keys rejected;
- lint, defect lint, distribution, diversity, profile floor, self-check,
  rule smoke, grammar, Racket lint, and authority synchronization: green;
- full semantic smoke: 600/600 materializations, 305/600 witness hits, 60/60
  rival claims checked, and no semantic defect; its wrapper exits nonzero only
  because any declared schedule period emits the generic
  `declared_period_not_enumerated` follow-up warning;
- explicit period census: all 12 fixed-seed band/residue lessons and all 60
  query rotations green;
- 100-per-band census: all 300 production lessons and 1,500 rotations green.

### Known limits

The generated grammar is intentionally bounded to three equal-width panels,
heights 5–8, widths 4–7 per panel, free polyominoes of 3–7 cells, one color per
panel, and at most one separated singleton per panel. The finite rival set is a
strong regression contract, not a proof against every conceivable hypothesis.
The exact-period census exhausts residues only at one fixed seed, while the
300-lesson census samples broader seeds rather than all possible inputs.

Imported associated notes retain their original evidence in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4c969fc26956568436a826318dacab429db49f3aa709881a142ee8232bd1da6e`.

# Decisions: 1cbcf1ed9a32

Final generator SHA-256:
`4c969fc26956568436a826318dacab429db49f3aa709881a142ee8232bd1da6e`.

## D1 — Preserve the Racket authority and add the missing pin

**Choice.** Leave the synchronized Racket transformation unchanged and set
`RULE_HASH = "dc0d41aa47ba"`.

**Original rationale.** Unknown. The v1.4 generator omitted the required pin,
but its baseline `rule_smoke`, `racket_lint`, and `authority_sync` stages were
green, and an independent Python mirror reproduced every canonical output.

**Alternatives.** Rewrite or broaden the Racket rule; make the Python mirror a
second authority.

**Why rejected.** No output defect was found. Changing a correct authority would
add risk without improving the input curriculum. `rule_mirror` is retained only
for tests and semantic probes.

**Evidence.** `checks/before/`, `checks/rule-smoke-after/`, and the final after
battery. No reference-rule file changed.

## D2 — Replace stale controls with six exact axes

**Choice.** Retire `shape`, `d4_variant_idx`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture`. Keep exact controls for dimensions,
common size/pair, palette family, and optional secondary objects.

**Original rationale.** The old comments described broad combinatorial control,
but several axes were singleton, ignored, aliases, or incompatible with the
actual difficulty ranges. The legal texture domain also included malformed
inputs.

**Alternatives.** Preserve every historical name as a compatibility alias; make
all old low-level knobs independently composable.

**Why rejected.** Silent aliases and no-op controls were the primary override
failure. There was no retained external contract requiring them, and preserving
them would leave a misleading Cartesian product. The new surface is smaller but
fully observable.

**Probe.** The exact override battery accepted 20,160/20,160 draws across 224
cases and all bands, with no findings or warnings. Task tests reject unknown keys,
booleans, floats, invalid enums, invalid difficulty, and retired axes.

**Limit.** An undocumented caller using an old key now receives an explicit
error rather than an unrelated grid. That fail-closed incompatibility is
intentional.

## D3 — Give all three largest objects the same cell count

**Choice.** Draw the common class and distractor from different D4 classes of the
same `common_cells` value.

**Prior choice.** Version 1.4 deliberately chose a distractor with a different
cell count to guarantee a distinct D4 class.

**Reason for reversal.** Different counts make shape comparison unnecessary.
The hybrid rival “select a member of the repeated cell count; otherwise panel 0”
fits all canonical labels and every ordinary v1.4 draw.

**Alternatives.** Keep unequal sizes but add a few equal-size special textures;
allow any size relation randomly.

**Why selected.** Equal sizes remove the shortcut from every ordinary generated
case, not merely occasional witnesses, while distinct canonical classes still
guarantee a unique intended answer.

**Probe.** Every focused test draw has one shared largest-object size and exactly
two matching D4 signatures. The retained source-bound counterexample is
`repo/generators/1cbcf1ed9a32/counterexamples/repeated_cell_count_else_first_panel.json`.

## D4 — Enumerate free polyomino classes through seven cells

**Choice.** Build all free polyomino classes of sizes 3–7 recursively, verify the
known class counts `2, 5, 12, 35, 108`, and filter by the selected panel envelope.

**Prior choice.** Version 1.4 mixed a fixed bank with stochastic random walks and
a fallback L-tromino.

**Alternatives.** Retain the 12-shape bank; continue rejection-sampled random
walks; expand to larger shapes.

**Why selected.** Enumeration is deterministic, prevents fallback bias, permits
same-size distractors by construction, and substantially expands output variety
without exceeding the small canonical-like canvas. Sizes above seven would make
the exact override cross-product harder to guarantee in 4×3 placement envelopes.

**Probe.** The module verifies class counts at import. Focused lint measured 68
distinct outputs across 144 labeled pairs (47%) with no diversity warning.

**Limit.** This is not the universe of shapes beyond seven cells, and envelope
filtering makes some classes unavailable at the smallest dimensions.

## D5 — Use a deterministic four-slot teaching schedule

**Choice.** Declare a period-four schedule with profiles
`canonical_panel0_distractor`, `expanded_alternate_pair`,
`expanded_panel0_distractor`, and `expanded_pair01`.

**Original rationale.** The v1.4 comments wanted four examples spanning all
distractor positions, but ordinary random generation did not guarantee this.

**Alternatives.** Pure random common-pair sampling; rejection-sample each whole
lesson; use three or five slots.

**Why selected.** Four slots match `EXAMPLES_NEEDED = 4`, guarantee a
panel-0-distractor witness in every demonstration window, retain a canonical
5×14 anchor, and remain simple enough to enumerate exhaustively. The final
defaults deliberately decouple `common_cells` from `panel_w`; an earlier draft
made them move one-for-one and triggered distribution lint.

**Probe.** `checks/schedule-period-s0.json` exhausts all four residues at seed 0
in all three bands: 12 lessons, 60 query rotations, zero ambiguities. The wider
`checks/lesson-census-100.json` covers 300 lessons and 1,500 rotations with zero
ambiguities.

**Failure mode.** A deterministic schedule can alias with an external sampler
that skips indices. Exact overrides remain available, and the declared period
makes the policy inspectable rather than implicit.

## D6 — Include exact palette and secondary-object variation

**Choice.** Supply four disjoint three-color palette sets and either no secondary
object or one same-colored singleton in every panel, separated by a blank row.

**Original rationale.** The old palette family was nominally varied; the
`two_objects_per_panel` case was placed among degenerate textures despite being
lawful under the largest-object rule.

**Alternatives.** Remove all secondary objects; allow arbitrary clutter; vary
palette size.

**Why selected.** Singletons teach that the largest component is causal without
introducing ties or uncontrolled segmentation. Fixed three-color families make
`palette_kind` exactly observable. Arbitrary clutter would broaden the rule's
input grammar without canonical support.

**Probe.** `observe_overrides` round-trips both controls for the full exact
matrix; mutation tests reject inconsistent modes, color reuse, largest-object
ties, and malformed clutter.

## D7 — Make shortcut claims executable

**Choice.** Declare `first_panel` and
`repeated_cell_count_else_first_panel` as semantic rivals, canonical shortcuts,
and lesson competitors. Declare `panel_zero_distractor` as the witness for both.

**Original rationale.** Version 1.4 named informal rivals only in comments.

**Alternatives.** Depend solely on generic shared-tool rivals; list rival names
without executable functions.

**Why selected.** Executable competitors can be checked against every canonical
pair, every generated demonstration, and every query rotation. The second rival
captures the strongest historical distribution shortcut rather than only the
simpler “always panel 0” rule.

**Probe.** The semantic smoke verified 60/60 rival claims and found the witness in
305/600 generated inputs. Both larger censuses report zero production or
rotation ambiguity.

**Limit.** Passing a finite named-rival set does not establish unique induction
against all possible hypotheses.

## D8 — Strengthen structural validation and source-bound tests

**Choice.** Require rectangular integer grids, exactly two divider columns,
three equal panel widths, color 5 only on dividers, one color per panel, distinct
panel colors, a unique largest component, consistent secondary-object mode,
equal largest-object sizes, and exactly one repeated D4 class.

**Original rationale.** The old validator selected `max` without rejecting ties,
did not fully constrain panel widths/colors, and accepted inputs outside the
claimed generated manifold.

**Alternatives.** Validate only what the Racket function needs; treat malformed
examples as diagnostic textures.

**Why selected.** Training admission should reflect the documented grammar and
make every advertised axis observable. Invalid diagnostics belong in mutation
tests, not the ordinary generation domain.

**Probe.** Fifty task-local tests pass, including malformed grids, mutations,
determinism, global RNG purity, canonical ownership, exact overrides, schedule
windows, query rotations, and the retained counterexample.

## D9 — Keep the schedule declaration despite the semantic-gate warning

**Choice.** Retain `LESSON_SCHEDULE_PERIOD = 4` and satisfy the requested
follow-up with explicit period enumeration, rather than deleting the declaration
to make the smoke wrapper exit zero.

**Reason.** The semantic gate currently emits `declared_period_not_enumerated`
for any declared period because it cannot consume an external census receipt.
Removing the declaration would hide useful contract information and game the
check.

**Evidence.** The final semantic smoke otherwise reports 600/600 successful
materializations, zero semantic defects, 305 witness hits, and 60/60 rival
claims. `checks/schedule-period-s0.json` explicitly enumerates all period
residues and is green; `checks/lesson-census-100.json` provides broad random
coverage.

**Limit.** The full after-battery aggregate remains nonzero solely for this
shared-tool follow-up warning; it is reported rather than suppressed.

## D10 — Retain a source-bound two-setting parametric family

**Choice.** Keep the approved production generator and canonical Racket program
byte-identical. Add a task-local native adapter with `canonical_shape` as the
exact default and `selector_member` as the alternative setting.

**Sequential dependency.** Step A compares the three largest objects up to D4
and retains the repeated-shape pair in left-to-right order. The intermediate is
that ordered pair. Step B uses selector 1 or 2 to choose a pair member and emits
its observed normalized orientation. The selector is ordinal within the pair,
so an absolute panel cannot be chosen before Step A.

**Evidence.** `workspace/parametric/evidence/current/teaching-audit.json` covers
320 teaching jobs, 2,560 generated pairs, demo counts 2–6, four queries per
job, and 320 exact 30×30 query cases. Native qualification at
`checks/1cbcf1ed9a32/qualification/qualification.json` qualifies both settings
on seeds 0 and 17 through 40 protected-Racket labels. The source-bound
counterfactual at `checks/1cbcf1ed9a32/causal/witness.json` changes the retained
pair from `[1,2]` to `[0,1]` and changes the final output.

**Status and limit.** Reviewer scope is ready; owner acceptance and training
admission were not performed. The finite rival audit is not a proof against all
hypotheses or a measured training-gain claim.
