# Working notes: 2c6496d261a6

## Review 133862fbfa7d5f89

The original associated-note ledger and working note were empty templates; no
prior substantive decision or return was available. The selected canonical rule
and all four canonical input/output pairs agree on global row confinement, so
the rule and archival authority were not edited.

Baseline generator SHA-256:
`c77e307d30b565e37514c31eb89729affbd5e99de6b9c40d52be8657474f7702`.
Repaired generator SHA-256:
`6ac6a1032c153b6a8f7b4dbe1edb39ae423ce4397908a3c88f74b61bca4d62f7`.

## Reproduced defects and decisions

- Baseline seed 38, index 0, `kept_colors=3` produces only two keeper colors:
  one keeper can overwrite another. Reserve each role's minimum empty cells
  before optional extensions, and recover axis observations from final pixels.
- Ordinary baseline construction tries to give each distractor two occurrences
  in two rows. The wrong rule "keep a singleton or a color repeated within any
  row" fits all four canonical pairs and all 2,000 measured ordinary inputs.
  This is not a full-support claim: an explicit `single_color_total` degenerate
  control already separates the rival, and a failed placement retry can retain
  a partial write when a row is full. A primary distractor now reliably has at
  least three rows and a repeated row, directly challenging that rule in ordinary
  mixed lessons rather than depending on a special control or placement failure.
- The old advertised controls include ignored options and inconsistent bounds.
  Four exact independent integer axes replace them. Unknown keys, noninteger
  values, conflicting palette aliases, and impossible palette/keeper relations
  reject explicitly; no clipping or silent fallback supplies a different grid.
- Width 7 is the constructive lower bound across all supported palette/keeper
  combinations. On a 3x7 canvas, palette 9 and keeper count 1 use at most 20
  occupied cells, retaining background and the required witnesses.
- An initial repair passed a 40-lesson smoke but only 397/400 larger measured
  lessons. Three easy lessons omitted singleton keepers from demonstrations;
  both queries then separated the surviving `drop_singletons` rival. Ordinary
  sampling now reserves a singleton keeper. The explicit one-keeper/two-color
  controls remain legal and may truthfully fail the full teaching hook.
- The full battery then exposed an acceptance-only validator and palette-alias
  provenance issues. `_grid_errors` validates physical ARC grids, `self_check`
  requires the mixed keeper/distractor curriculum, and `strict_canonical_like`
  adds a horizontal multi-cell keeper. Outputs and query grids use physical
  validation in the lesson hook. The palette alias is declared separately and
  normalized before keyed axis selection, including alias-only calls.

## Executable semantic contract

The seven named rivals are `row_repeat_or_singleton`, `erase_two_occurrences`,
`erase_two_rows`, `column_confined`, `drop_singletons`, `identity`, and `erase_all`.
The first three fit all four usable canonical pairs. Five witnesses inspect
actual pixels: global row conflict, a three-row color, a horizontal keeper, a
singleton keeper, and kept/erased colors sharing a count of at least three.

`lesson_identifiable` requires the demonstration labels to refute every declared
rival. It does not read query outputs. Conflicting labels for an identical input,
shape changes, and recoloring are rejected. Racket supplies authoritative labels;
production contains wrong rivals, not a replacement correct-label implementation.

## Retained verification

Evidence is in the return for assignment `review-133862fbfa7d5f89`:

| Evidence | Result and scope |
|---|---|
| `checks/after-final/result.json` | 12/12 battery stages green, no advisories |
| `checks/tests-final-v2/` | 50 focused tests pass, including actual Racket |
| `checks/lesson-probe-final.json` | 400/400 ordinary lessons refute all seven rivals; 2,000 distinct inputs |
| `checks/lesson-probe-baseline-final.json` | Same evaluator: 0/400 baseline lessons refute all rivals; 2,000 distinct inputs |
| `checks/lesson-initial-100.json` | Retained 397/400 intermediate result with exact failing lessons |
| `checks/iterations/` | Source snapshots for the retained intermediate failures |
| `checks/code-review/` | Independent review of final source and focused alias/domain checks |

The larger probe uses 100 lessons in each of default, easy, medium, and hard,
with three demonstrations and two queries per lesson. Each canonical-fitting
shortcut disagrees with actual Racket on all 2,000 repaired inputs and none of
the 2,000 baseline inputs. `probe_completed`/`passed` mean computation completed;
`all_lessons_identifiable` is the separate semantic outcome.

## Limits and handoff

Ordinary lessons emphasize mixed roles, a singleton, and a three-row conflict;
they do not cover all reference-lawful grids. Identity, all-erased, and all-zero
cases remain Racket regression fixtures but are outside the mixed curriculum.
Canvases narrower than seven are unsupported. Optional same-count witnesses
need spare capacity and are not promised on every exact-control grid.

The seven-rival result does not establish universal learnability. Add a concrete
new rival and counterexample before claiming a new support gap is resolved. See
`workspace/README.md` for commands and `workspace/NEXT_REVIEW.md` for source and
evidence checks. The post-repair solve declared prior rule exposure; both solve
records reported 3/3 visible demonstrations, with masked correctness withheld.
No approval or training-admission upgrade is claimed.
## Current reviewer considerations

Source SHA-256: `6ac6a1032c153b6a8f7b4dbe1edb39ae423ce4397908a3c88f74b61bca4d62f7`.

# Decisions for 2c6496d261a6

## Scope and authority

The assigned task retains every occurrence of a nonzero color exactly when that
color occupies one distinct row. The existing canonical Racket rule implements
that rule and its four stored input/output pairs agree with the written task.
The repair changes the input sampler and task-local verification only. The
assignment, canonical ledger, archival authority, and approval state stay bound
to the packet. There is no prior task-local return or substantive note to use as
a repair lead; the imported note and associated-note ledger are empty templates.

## D1: Replace overwriting placement with reserved empty cells

Original rationale: unknown. The original keeper loop draws a row and arbitrary
columns independently for every color, then writes over existing contents.
The baseline seed 38, index 0 with `kept_colors=3` actually contains two keeper
colors. Repeatedly retrying a damaged grid would hide this defect and make exact
controls conditional on luck. The repair reserves the minimum cells for every
role first, then adds optional cells only to empty positions. Color counts are
recovered from the completed grid by `observe_overrides`, rather than reported
from construction intent.

## D2: Retain a small set of exact controls

`grid_h`, `grid_w`, `kept_colors`, and `palette_size` are four independent
controls observable from pixels. `n_distinct_colors` is an accepted compatibility
alias for palette size, declared separately from the independent axes. Conflicting alias values and requests with keepers greater than or
equal to the total palette are incompatible, with named axes on the exception.
A single exact control must remain usable: the unspecified counterpart is drawn
from the compatible domain. None of these controls silently clips its value.

The prior palette-kind, texture, position-bias, and density declarations do not
control the baseline draw. They are removed and unknown keys fail explicitly.
Implementing additional palette taxonomies would add interface complexity without
helping the row-confinement lesson. Lawful all-kept, all-erased, and all-zero
inputs remain valid for the physical shape/value validator and Racket regression
fixtures, while `self_check` rejects them outside the mixed generator curriculum;
the former fixed degenerate texture branches are not ordinary training draws.

The width domain becomes 7..18, and height remains 3..12. Width 7 includes the
smallest canonical width. At the smallest 3x7 canvas it also permits up to nine
colors with one horizontal keeper, eight distractors, an expanded three-row
witness, and at least one background cell. The previously advertised width 5
was not accepted across difficulty bands, and the wider constructive lower bound
avoids a large, fragile geometry-incompatibility table. Kept colors range 1..5;
total colors range 2..9, subject to kept < total. Numeric bool/float/string inputs
are rejected rather than coerced.

## D3: Generate the missing semantic cases

The ordinary baseline constructor tries to place two cells per distractor in
different rows. “Keep a singleton or any color with a repeated row” fits all four
canonical pairs and all 2,000 measured ordinary baseline inputs. The repair gives
one primary distractor cells in at least three rows, with at least two cells in
one of those rows. A primary keeper has multiple cells in its sole row. Both
roles use randomly drawn colors, positions, and column layouts.

The baseline already has an explicit `texture="single_color_total"` control with
four same-color cells across two repeated rows; that fixed degenerate input
separates the local-repetition rival. Ordinary placement is also nontransactional:
if its second row is full, the first cell remains before a retry, so an unusual
ordinary draw can acquire additional distractor occurrences. The review therefore
claims measured weakness of ordinary lessons, not impossibility of any baseline
counterexample. The repair makes the distinction reliable in normal mixed lessons
and eliminates partial writes through the same empty-cell reservation design.

Remaining colors add singleton keepers, varied horizontal runs and gaps,
two-row distractors, aligned and unaligned pairs, and optional extra occurrences.
When capacity permits, keep and erase colors can have equal counts of at least
three. This prevents simple frequency and horizontal-repeat heuristics from
being the only explanation of a generated lesson. The smallest fully packed
control cases retain the required minima and can have fewer optional features;
no optional extension is falsely advertised as an exact control.

## D4: Preserve a canonical-size component while widening support

Difficulty affects sampling weights, not the override domain. Each band mixes
new random layouts near canonical size/palette with broader layouts. All declared dimension values remain drawable in ordinary sampling. Ordinary
cardinalities are 3..9 total colors and 2..5 keepers; the 2-color and 1-keeper
limits remain supported through explicit overrides. Canonical inputs are not
replayed, and no finite counterexample bank supplies ordinary samples. The core
component protects profile support; the broader component varies grid size,
number of roles, density, and occurrence counts. A source-bound probe reports
actual dimensions, witnesses and unique input counts rather than treating these
weights as evidence of coverage.

## D5: Make the semantic claim executable and finite

The semantic contract has a lawful-grid validator, a stricter mixed teaching
domain, pixel-derived witnesses, executable rivals, and a lesson hook. The hook
requires demonstrations to refute every named competitor; it does not inspect
query labels or pretend a finite rival family proves universal induction.
Racket remains the label authority. The task-local lesson probe uses actual
assembled generator episodes, all declared rival names, and both query inputs;
it separately records refuted rivals, survivors agreeing on queries, and survivors
that disagree on a query. Reported sample counts identify their exact sampler,
source hashes, seeds and uniqueness denominator.

## Limitations and next useful extension

The ordinary family intentionally emphasizes mixed keep/erase lessons and a
three-row global conflict. Identity/all-erased lessons and canvases narrower than
seven are outside ordinary sampling. Remaining possible shortcuts, such as a
new cutoff on larger row spans, must be measured against explicit counterexamples;
the finite competitor result is not a proof that every learner will infer the
rule. A future extension should add a concrete rival and a source-bound lesson
probe before broadening a distribution simply to make its histograms larger.

## D6: Preserve the intermediate lesson failure and fix the sampling cause

The first 40-lesson smoke passed. Extending the actual Racket-backed sampler to
100 lessons per band found three unidentifiable easy lessons: seeds/index starts
(1002716,75), (1002772,355), and (1002781,400). Their demonstrations contained no
singleton, while both queries did, so the declared `drop_singletons` competitor
survived. The initial source is retained at `checks/iterations/initial_generator.py`
and the full result at `checks/lesson-initial-100.json`.

The revision selects at least three total colors and two keepers for ordinary
draws, reserving keeper index 1 as a singleton. Exact palette-size 2 and
keeper-count 1 remain legal explicit requests; their lessons may truthfully fail
the full teaching hook. This removes the observed failure by construction instead
of increasing examples until a random test sample becomes green. The separate
lesson-hook regression also rejects identical demonstration inputs with conflicting
outputs and rejects shape changes or recoloring; labels themselves still come
from the unchanged Racket authority.

## D7: Distinguish mathematical validity, curriculum validity, and aliases

The first full after battery rejected an acceptance-only `self_check` and a
palette alias advertised as a second independent axis. These failures are retained
in `checks/after/`. The revised `_grid_errors` checks physical grid validity;
`self_check` additionally requires both a one-row color and a multi-row color;
`strict_canonical_like` additionally requires a horizontal multi-cell keeper.
The canonical four inputs satisfy all three levels. The lesson hook validates
demonstration outputs and query grids physically, so an all-zero output is never
wrongly rejected as an invalid lesson.

The independent AXES now contain just one palette-size control. Its historical
`n_distinct_colors` spelling is accepted through `AXIS_ALIASES`, with both requested
spellings consumed and the canonical palette axis recorded even for an alias-only
call. This preserves useful compatibility while removing a false independent
variation claim. No shared gate is disabled or weakened.

## Review e9d552543e859448: native row-selection family

The approved base generator and canonical rule were retained unchanged. The native
family fixes an episode-level `row_selection` parameter with two settings:
`one_row_only` is the exact catalog-selected canonical program, while
`fewest_rows` counts the distinct rows occupied by each nonzero color, derives
the minimum count from the input, and retains every color attaining it.

The first two-demo construction allowed a plausible `fewest_cells` rival to fit
both visible examples and fail a query. I repaired the teaching inputs rather
than adding demonstrations: the minimum-row role is now denser than the next
role, so row count and cell count induce different choices. A later 50-seed sweep found a second teaching confound at seed 9: `top_row`
fit both visible `fewest_rows` demonstrations and failed a query because the
minimum-row role was always anchored at row zero. The next-higher row-count role
now also spans the top and bottom rows, constructively refuting that shortcut.
The retained bounded audit covers seeds 0, 9, 17, and 97 for both settings and
reports eight cases with no query-changing survivor among the declared rivals.

The family supports 2–6 demonstrations and 1–4 queries with matched,
deterministic, prefix-stable inputs. Its four-query schedule ends in a substantive
30x30 input. Protected Racket authoring preflight passed four jobs and 32 labels;
the wrong-threshold counterfactual was replayed under protected Racket. Sixteen
one-query public views passed 24 private-field invariance checks and four visible
positive controls. Owner review, native qualification/acceptance after
integration, and training admission remain separate actions.
