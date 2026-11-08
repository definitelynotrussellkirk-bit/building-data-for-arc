# 4e081a15d785 — current generator decisions

## Authority and intended behavior

Version 2.0.0 follows the unchanged selected Racket program `(rule! (compress-grid g))`,
normalized rule hash `0805714fcf25`. The primitive removes consecutive identical
**whole rows**, then consecutive identical **whole columns**. A horizontal equal
run in one row does not justify deleting a column when another row distinguishes
it. Nonconsecutive repeated rows and columns remain. This is the executable
contract; the canonical record's inherited `written_solution` says rowwise run
compression and is misleading. That shared metadata is outside this task delta.

The predecessor's independent row expansion and validator described that rival.
All six canonical pairs fit both interpretations, so canonical agreement alone
could not expose the mismatch. The 3×4 input in
`counterexamples/whole_columns_vs_rowwise.json` was executed through the supported
Racket apply command and yields a 2×3 output, while the rowwise rival yields 2×2.

## Domain and controls

Inputs are rectangular grids of integer colors 0..9 with at least two realized
colors. The validator permits 1..30 rows/columns; sampling controls cover 1..18
rows and 1..22 columns. A one-row or one-column multicolor grid is legitimate.
The default sampler always performs at least one actual compression. Explicit
multicolor identity cases remain available through exact zero-deletion controls;
`ALLOW_IDENTITY_OUTPUT=True` applies to those research cases.

The exact controls are `grid_h`, `grid_w`, `base_color_count` (2..10),
`n_duplicates` (full rows removed), and `n_column_duplicates` (full columns removed).
For requested dimensions h,w and deletion counts dr,dc, the latent core has shape
(h-dr)×(w-dc); both dimensions must be positive and its cell count must accommodate
all colors. Infeasible joint pins raise a ValueError carrying `incompatible_axes`.
Unknown keys and coercible nonintegers are rejected. None retains no-override
semantics. `observe_overrides` recovers every declared value from returned pixels.

Removed controls: `palette_kind`, `color_sequence_kind`, `anchor_endpoints`,
`duplicate_position_bias`, and `texture`. They were overlapping descriptions,
ignored controls or degenerate aliases rather than reliable observable contracts.
The meaningful original dimension/palette/row-deletion controls remain; column
count is now explicit. Callers using retired controls receive a clear error.

## Distribution and teaching policy

The default semantic schedule repeats every four sample indices:
**rich witness, rich witness, canonical stripe anchor, broad sample**. Three
consecutive demonstrations and one query contain two rich examples, so holding
out any pair still leaves a rich demonstration. The census also checks actual
accepted indices, duplicate rejection and query rotations; the schedule argument
alone is not a claim about arbitrary resampling or fewer demonstrations.

Rich cores have variable height, width, palette, reflection and row/column run
lengths. Each preserves local equal neighbors inside globally different columns,
separated repeated columns, and separated repeated rows. A separate broad random
core component avoids restricting every non-stripe example to this template.
Canonical anchors reconstruct the six original shape/palette profiles with fresh
palettes and run lengths. Every band retains that component. The conservative
`strict_canonical_like` hook identifies stripes; it does not relabel every broad
lawful sample as canonical-like.

The generator declares three canonical-fitting shortcuts and six lesson rivals.
The former are rowwise run compression (padding ragged rival results by their
last color), first-row-only column boundaries, and global column uniqueness.
A lesson hook reports any declared rival that fits all demonstrations but changes
the query. Whole-row and whole-column compression commute, so reversing those
whole-line operations is not falsely declared a distinguishing rival.

## Reversals, evidence and limits

An intermediate candidate admitted monochrome grids and sampled identity cases.
The full battery exposed the resulting low-value defaults and non-probative
mutation checks. The final policy excludes monochrome training grids and makes
actual default compression constructive; legal multicolor identity overrides
remain. An explicit witness was added for the first-row rival instead of relying
on a merely related predicate. The original and intermediate failures remain in
the return's `checks/` receipts.

Current focused tests are `tests/test_compression_contract.py`; the reusable
Racket-backed probe and its instructions are in `workspace/`. Final production,
rotation, profile and source-hash counts live in the return's REVIEW/RESULTS and
checks, rather than a cumulative history here. No prior review_index or actionable
audit was present in this task's supplied home. The two newly drawn audits target
other tasks and are not implicitly resolved by this repair.

Limitations: finite declared rivals cannot establish universal identifiability;
explicit overrides can remove the default lesson witnesses. The training domain
intentionally excludes lawful monochrome cases. Canonical text remains stale
until a maintainer chooses the shared metadata correction. No rule change or
training-trajectory admission is proposed.

The final generic defect lint still flags 12/50 mutation rejections and accepted
singleton, 2x2-block and short-line probes. These multicolor rectangles are lawful
for whole-line compression. `workspace/probe_lawful_mutations.py` retains the exact
shared mutations and Racket outputs without changing the gate verdict. A shared
semantic disposition remains open. The supported interchange is JSON grids;
mixed Python list/tuple row containers are accepted by the validator but can make
row-equality observations container-sensitive. Generated and JSON canonical grids
use lists consistently; normalizing mixed containers is a minor follow-up.

## Current maintainer interpretation

The unchanged `compress-grid` reference deduplicates adjacent whole rows and, after transposition, adjacent whole columns. Canonical prose now states that rule explicitly. The generic defect-lint warnings remain observations: accepted singleton, solid and short-line rectangles can be lawful inputs for this task, so those observations alone do not establish a semantic defect. This interpretation is limited to the returned generator SHA-256 `73014e825e86d3119866574d1b70b9c38862c869b2838ff276ecd01551ee165e` and rule `0805714fcf25`; it creates no lint waiver and the reported 11/12 battery result stays visible. Reviewer-provided Racket witnesses are retained, not rerun at intake. The unrelated `defba1ab4f90` archival digest mismatch remains open; no fixture was changed. Model trajectories remain unadmitted.
## Current reviewer considerations

Source SHA-256: `73014e825e86d3119866574d1b70b9c38862c869b2838ff276ecd01551ee165e`.

# Decisions — 4e081a15d785

Selected generator version **2.0.0**, SHA-256
`73014e825e86d3119866574d1b70b9c38862c869b2838ff276ecd01551ee165e`.
The unchanged canonical program is `(rule! (compress-grid g))`, normalized rule
hash `0805714fcf25`. Paths below are relative to `WORK/`.

## Authority, input grammar and construction

The executable authority removes consecutive identical **whole rows** and
**whole columns**. The predecessor described and constructed independent
horizontal run compression. Its comments suggest the inherited canonical
`written_solution` motivated that interpretation; earlier author intent is
otherwise unknown. All six labeled canonical pairs fit both rules. The supported
Racket disagreement is retained in `checks/authority/{input.json,racket.json}`.
The shared canonical wording remains misleading; this repair does not change
the canonical program, primitive, or shared metadata.

| Choice | Predecessor / alternative | Current reason and tradeoff |
|---|---|---|
| Rectangular integer colors 0..9, at least two realized colors | Predecessor required horizontal runs, a repeated row, output width ≥2 and ≥2 colors | Full-line compression is valid for arbitrary rectangles; artificial output-width and shape restrictions exclude canonical cases. `self_check` permits sides 1..30 and rejects ragged, invalid-color and monochrome training inputs. |
| Thin multicolor inputs are legal | Predecessor forced width ≥3 and at least two base rows | Canonical outputs are commonly one row or one column. Explicit controls also permit one-row/column inputs. No distinguished background color is imposed. |
| Shared row/column expansion of a core | Independently chosen run lengths in every row | One column repetition length applies across all rows. A core with distinct adjacent full lines gives exact deletion counts and rectangular authoritative outputs. Local equal cells may remain inside distinct full columns. |
| Constructively feasible cores | Rejection-only sampling or clamping incompatible pins | Random cores use bounded retries, followed by a checkerboard construction with distinct extra colors. Positive shared run lengths realize the requested dimensions. Infeasible pins fail explicitly rather than changing their meaning. |
| Every default draw actually compresses | First intermediate candidate sampled identities and admitted monochrome cases | Intermediate battery findings led to constructive default deletion and exclusion of monochrome training grids. Lawful multicolor identity overrides remain available; `ALLOW_IDENTITY_OUTPUT=True` covers them. |

## Exact observable controls

| Control | Current contract | Prior behavior and reversal |
|---|---|---|
| `grid_h` | Exact returned height, 1..18 | Previously a size hint for choosing base rows; inserted copies could change the final height. |
| `grid_w` | Exact returned width, 1..22 | Previously forced to at least three; the advertised domain and actual draw bounds differed. |
| `base_color_count` | Exact realized color count, 2..10 | Previously truncated by palette pools, so requested and realized counts could differ. All colors, including zero, may participate. |
| `n_duplicates` | Exact number of adjacent full rows removed, 0..17 | Previously insertion count was clamped to at least one; zero was not honored. |
| `n_column_duplicates` | Exact number of adjacent full columns removed, 0..21 | Newly explicit: horizontal run inflation was previously row-local. |

For dimensions `h,w` and deletion counts `dr,dc`, the core dimensions are
`h-dr,w-dc`. Both must be positive and their product must accommodate the
requested colors. Jointly infeasible pins raise `IncompatibleOverrides` with
`incompatible_axes`; bools and coercible nonintegers are rejected. `None` means
no override. `observe_overrides` recovers the five controls from pixels.

Retired keys are `palette_kind`, `color_sequence_kind`, `anchor_endpoints`,
`duplicate_position_bias` and `texture`. Palette, sequence and bias choices
affected predecessor sampling but did not provide reliable exact observable
contracts; `anchor_endpoints` was unused, and texture aliases mixed constructive
choices with degenerate fixtures. Retaining decorative controls or silently
ignoring them was rejected. Unknown/retired keys now fail clearly. The earlier
reason for every advertised control and range is not documented.

## Distribution and teaching

The four-slot default schedule is **rich witness, rich witness, canonical stripe
anchor, broad sample**. Rich cores vary dimensions, palette, reflection, extra
rows/columns and shared repetition lengths. They preserve locally equal cells
in globally distinct columns and separated repeated full rows/columns. Two rich
slots make a consecutive four-pair window retain a rich demonstration after
any one pair is held out.

Canonical anchors reuse six shape/palette-cardinality profiles with fresh colors
and repetition lengths, rather than copying the original grids. They retain
tiny stripe support in every band. `strict_canonical_like` conservatively accepts
grids with all rows identical or every row monochrome; it does not equate broad
lawfulness with canonical resemblance. A separate random-core component avoids
making the rich template the entire non-stripe distribution. Difficulty scales
rich cores; canonical anchors and broad samples retain their small scale.

| Default component | Concrete sampling choice | Reason / limit |
|---|---|---|
| Rich witness | Core height 3..4/6/9 and width 4..6/8/12 for easy/medium/hard; colors 2..min(8, core width−2); add 1..4 row and column copies | The fixed first four core columns and first three rows prove the local-run and separated-repeat distinctions; variable extension/reflection prevents a single fixed grid. Witness geometry still forms a template, hence the other components. |
| Canonical stripe | `(height,width,color count)` profiles `(4,2,3)`, `(3,3,3)`, `(3,5,4)`, `(6,4,4)`, `(3,3,2)`, `(4,9,5)` | Retain the original tiny scale and stripe arrangements, including separated row recurrence and single-axis identity. Shapes are intentionally shared across difficulty bands. |
| Broad sample | Height 2..6, width 2..9; choose positive core dimensions of area ≥2 with at least one smaller side; colors 2..min(5, core area) | Construct actual deletion without imposing the rich pattern on every lawful grid. Broad profiles can incidentally also be stripes. |
| Explicit pins | Sample feasible remaining dimensions/deletion counts over declared ranges; construct a general core | Honor pins exactly. This path intentionally does not inherit scheduled witnesses or difficulty-dependent rich bounds. |

Every draw uses the versioned keyed context and a keyed construction RNG; no
cross-call state or bare global randomness is needed. Version 2.0.0 intentionally
changes the seed-to-grid mapping from the predecessor. Shared expansion lengths
are positive random partitions, allowing asymmetric and unequal run lengths
without independent-row boundary drift.

Three demonstrations plus one query are required. The lesson hook tests **six
distinct algorithms**: rowwise runs, first-row boundaries, global column
uniqueness, global row uniqueness, rows-only and columns-only compression.
The first three fit all canonical labels and are declared shortcuts. Duplicate
namespace entries are not additional algorithms. Reversing whole-row and
whole-column compression is answer-equivalent and is not declared a rival.
An explicit first-row-boundary witness replaced an insufficient related witness.

## Evidence, reproducibility and limits

- `checks/compression-probe.json`: 48 generated inputs plus two separate hand
  diagnostics labeled by public `Catalog.apply`; all canonical shortcut checks
  fit, all six algorithms have generated disagreements, and observed counts
  match Racket output dimensions. Each band has 16 distinct inputs and 7/16
  strict stripe support. Initial-source reports remain separately retained.
- `checks/lesson-census-final.json`: 300 materialized lessons, 1,200 pairs,
  1,200 held-out-query rotations and 1,185 distinct inputs; no materialization,
  scoring, hook or declared-rival ambiguity findings. This uses three demos and
  one query, consecutive requested starts, and actual accepted-index metadata.
- `checks/after-final/checks/4e081a15d785_after_battery_summary.json`: **11/12
  green; overall failed**. `defect_lint` retains the 12/50 mutation-rejection
  warning and accepted small-pattern warning. No suppression was applied.
- `checks/lawful-mutations/{input.json,racket.json,evidence.json,commands.json}`:
  six exact shared-helper singleton/block/short-line diagnostics accepted and
  executed successfully through Racket. Ragged, out-of-range and monochrome
  negatives are rejected. These cases support a source-bound semantic
  disposition, not an override of the failed gate.

Actual wrapper commands, run from the outer directory containing `review.py` and `WORK`:

```bash
python3 review.py run python3 generators/4e081a15d785/workspace/probe_compression.py --seeds 2 --samples 8 --out ../checks/compression-probe.json --hand-witness --require-witness
python3 review.py run python3 -m arcpuzzles lesson-census 4e081a15d785 --per-band 100 --rotate-query --period 4 --timeout 1800 --out ../checks/lesson-census-final.json
python3 review.py run python3 -m arcpuzzles check 4e081a15d785 --battery --require-rotations-identifiable --timeout 4000 --phase after --out ../checks/after-final
python3 review.py run python3 generators/4e081a15d785/workspace/probe_lawful_mutations.py --out ../checks/lawful-mutations
```

Use fresh output paths when reproducing. The first, second and fourth commands
exited 0; the battery exited 1. Final generator hashes match retained reports.

Rotations reuse each materialized four-pair bundle; they do not enumerate fresh
cyclic windows, alternative query assemblies, multiple-query lessons or fewer
demonstrations. Explicit overrides enter a separate controlled sampler and can
remove all scheduled witnesses. Duplicate rejection can advance accepted
indices, so the simple modulo argument alone is insufficient. Finite rivals,
sampled support and exact input hashes do not prove universal identifiability
or semantic diversity. The training domain excludes lawful monochrome cases.
JSON list grids are the supported interchange; mixed list/tuple rows can make
Python row-equality observations container-sensitive. Canonical wording and
the source-bound disposition of generic lint warnings remain follow-ups.
No rule change, approval grant or training-trajectory admission is proposed.

## Proposed `compression_axes` episode prototype — review-2dfa5e70ae8fd886

Added a task-local, **unapproved** parameter prototype under
`workspace/parametric/` without changing `generator.py`, the canonical ledger,
or the family approval state. The episode-fixed parameter is `compression_axes`
with bounded values `both`, `rows`, and `columns`; `both` is the exact canonical
`(rule! (compress-grid g))` source and remains the default. The two alternatives
remove consecutive duplicate whole rows only or whole columns only.

The retained evidence in
`checks/parametric/4e081a15d785-compression-axes-v1/` covers all three settings.
Each episode has three demonstrations and four distinct queries, every authored
input contains duplicate whole rows and columns, and demonstrations alone refute
both rival settings. All 21 episode labels plus all six canonical labels were
executed through the protected Racket bridge and replayed in a second pass. Public
challenge names are hashes of visible bytes only; seeds, settings, rule text and
query answers stay private. The writer sorts public IDs, rejects duplicate visible
challenges, fails closed on existing output, and caps episodes at 32 total pairs.

Focused task tests passed 110/110 across the existing compression contract and
new parametric contract. A bounded adversarial pass retained the 1-demo/31-query
limit, over-budget rejection, duplicate-visible rejection and public-tamper
rejection in `checks/parametric/4e081a15d785-adversarial.json`. This establishes
only the declared settings, seeds and teaching grammar; it does not approve a
production parameter, admit data, or claim support for arbitrary grids or rival
programs. The next useful maintainer action is to review whether the axis-only
alternatives are pedagogically valuable before any production integration.
