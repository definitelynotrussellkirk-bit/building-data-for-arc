<!-- native-gravity-current:start -->
## Current native gravity proposal

The separate `workspace/parametric/` implementation has four episode-fixed
gravity settings: down, up, left and right. It preserves stable order and
multiplicity along the selected axis. Down returns the selected canonical
program byte-for-byte; production source v3.1.0 remains unchanged at SHA-256
`6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9`.

Two constructive dense/sparse demonstrations contain a long gapped row and
column with movable gray cells, an unsorted repeated sequence and occupied
endpoints. Their different modal colors distinguish ordinary and conditional
five-cell-cap shortcuts. Counts independently support 2–6 demos and 1–4 queries,
with defaults 3 and 4. Matched inputs have independent stable prefixes and
constructively distinct shapes; four queries cover 30×30, 19×27, 1×30 and 30×1.
The sampler extends to the already-lawful full 1–30 ARC domain without altering
the production sampler or validator.

Fresh reviewer evidence: 145 task tests pass; native qualification covers 8 jobs
(four settings, seeds 0/17, three demos/four queries), 56 labels and 128 protected
Racket evaluations. The separate two-demo audit refutes 14 named rivals in all
8 episodes, exercises 20 edge cases and verifies 32 one-query public turn files,
using 164 protected evaluations in total. Runtime or rival-encoding errors
would fail that audit; no errors or survivors occurred. These checks remain
finite, not a universal uniqueness or measured training-gain claim.

The native causal replay changes only the count used by canonical `start`:
a 12-value sparse column starts at row 1 normally, versus row 8 under a count cap
of 5. Exact programs, intermediate values and changed outputs are retained in
`checks/2a43e4f3a796/causal/`. Source-bound inventory lives at
`workspace/parametric/evidence/manifest.json`; native qualification/execution
and self-audit evidence are retained in the return's main check directory.

Next action: integrate, then run native qualification and fresh owner acceptance
on exact live bytes. Reviewer-ready does not grant variant acceptance or
training admission. Historical production heuristic-gate failures and prior
resolved audit dispositions are unchanged and were not rerun as a new battery.
<!-- native-gravity-current:end -->

# Current decisions: 2a43e4f3a796

## Selected rule and source

Generator `3.1.0` has SHA-256
`6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9`.
The canonical rule remains `7b698fc27b90`; the canonical ledger and reference
program were not edited. For each column, collect every nonzero value in its
original top-to-bottom order, place that sequence against the bottom, and fill
the remaining upper cells with zero. Repeated colors retain their multiplicity
and order. Zero is the fixed background; gray `5` is movable foreground.

The rule is total on nonempty rectangular ARC grids of dimensions `1..30` with
integer colors `0..9`. Consequently, blank, singleton, full, one-row,
one-column, and already-settled inputs are lawful. `self_check` validates that
domain, including rejection of booleans and malformed grids. The sampling
bounds below are a narrower construction choice.

## Controls and ordinary distribution

| Control | Current contract |
|---|---|
| `grid_h` | Exact integer height, `3..24`. |
| `grid_w` | Exact integer width, `2..18`. |
| `active_cols` | Exact number of nonempty columns, `1..18`, bounded by width. |
| `n_distinct_colors` | Exact nonzero palette cardinality, `1..9`, bounded by occupied capacity. |
| `texture` | Diagnostic construction mode: `scattered`, `all_at_bottom`, `single_value_columns`, or `no_cells`. |

`palette_size` is a compatibility alias for `n_distinct_colors`, not a fifth
independent numeric axis. Conflicting aliases, infeasible joint counts,
unknown names, noninteger counts, and out-of-range values fail explicitly.
Previously ignored arguments are not retained as silent controls. `None`
values are treated as unset. Textures can overlap observationally; for example,
a scattered draw may already be settled. `single_value_columns` places one
nonzero cell in each active column. Positive count overrides conflict with
`no_cells`.

Ordinary draws follow the period-five cycle
`dense_teaching, sparse_teaching, dense_teaching, sparse_teaching, free`:
80% teaching and 20% free across a complete period. Both teaching modes have
height `7..24`, width `6..18`, all columns active, and a gapped column containing
`h-1 >= 6` nonzero cells. Dense inputs make a foreground color the unique mode;
sparse inputs keep zero the unique mode. Ordinary free draws use height
`3..24`, width `2..18`, singleton columns and a maximum of five cells per
active column. Exact overrides use the diagnostic construction path and require
their own lesson checks; the ordinary schedule guarantee does not apply to them.

The final schedule replaces the earlier three-demonstration design. With
`EXAMPLES_NEEDED=4`, every five consecutive raw indices contain two dense and
two sparse teaching inputs. Holding out any one pair leaves at least one of
each teaching type among the demonstrations. The sparse type addresses
`zero_modal_cap`: apply a five-cell capacity only when zero is modal. That
canonical-fit rival survived the first ten-rival checks because long columns
and foreground-modal scenes were coupled. The final declaration contains four
canonical-fit shortcuts and eleven distinct lesson rivals. The focused tests
now require a demonstration to refute every rival after each holdout, rather
than merely allowing a rival to agree on the entire bundle.

## Current evidence and limits

| Evidence | Result and scope |
|---|---|
| [Final battery](../../../checks/after-v31/result.json) | 10/12 stages pass; `selfcheck` and `defect_lint` remain failed. |
| [Portable task tests](../../../checks/task-tests-isolated-v31/result.json) | 60 passed; zero failures, errors, or skips. The earlier [prerequisite failure](../../../checks/task-tests-v31/result.json) ran no tests because isolated Python lacked pytest. |
| [Actual materializer census](../../../checks/lesson-census-v31.json) | 300 lessons, 1,500 distinct inputs, and 1,500 query rotations; no listed-rival ambiguity or execution/scoring errors. Labels were executed through Racket. |
| [Fixed-seed schedule census](../../../checks/schedule-census-v31.json) | Seed zero, all five starting residues across three bands: 15 lessons, 75 pairs, 75 required rotations, and nine globally unique inputs; no listed-rival ambiguity. |
| [Required-rotation semantic check](../../../checks/required-rotations-v31/result.json) | Passed under the required policy: 12 materialized lessons and 60 rotations, with no ambiguity, hook warnings, or errors. Assessment is against declared rivals. |
| [Final Racket witnesses](../../../checks/final-witnesses/comparison.json) | All 18 expected outputs match actual Racket: 12 authored endpoints/counterexamples and six ordinary dense/sparse inputs. Every input passes the validator; the sparse examples refute the conditional cap. |
| [Python distribution probe](../../../checks/distribution-v31.json) | 1,500 complete raw-index windows and 7,500 rotations; every one of the eleven distinct rivals refuted in every rotation. These are independent adjacent-swap diagnostics, without production materialization or Racket labeling. |

The two battery failures count lawful mutations and endpoint grids as impostors:
blanking, removing a color, adding an in-range color, or duplicating a row need
not leave the compaction domain. Their rejection-rate heuristics require shared
tool attention; the failures remain visible. The validator should not reject
valid compaction inputs to satisfy those heuristics.

Intake explicitly resolved the prior bottom-row audit
`review-0867d19380f40c97:v0001` against accepted source
`6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9`.
Its ignore-bottom-row shortcut was sampler-only and failed the canonical pairs.
The new teaching construction includes an occupied bottom cell; the 60-case
regressions, final probe and Racket census are reviewer-reported evidence for
that repair. The two generic validator-gate failures above remain open shared
policy feedback; this resolution does not make the full battery green.

Support is broad but does not enumerate the full rule domain. The schedule
argument concerns consecutive raw indices; the materializer census separately
checks accepted lessons. These checks establish finite evidence against the
listed rivals. No universal `lesson_identifiable` hook is declared, and no
universal identifiability or training admission is claimed.
[Current packet decisions](../../../DECISIONS.md) give the construction
reasoning. [Interaction counterexample evidence](../../../checks/interaction-before/review_evidence.json)
and its [Racket receipt](../../../checks/interaction-before/racket.json) retain
the superseded-source finding. Its larger historical boundary checks are not
claimed as final-source reruns. Imported associated notes remain in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9`.

# Current repair decisions: 2a43e4f3a796

## Outcome and authority

The selected generator is `3.1.0`, SHA-256
`6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9`.
It repairs missing bottom-row and singleton support, makes the retained controls
exact, and teaches both foreground-modal and zero-modal long columns. The
canonical rule remains `7b698fc27b90`. The canonical ledger SHA-256 remains
`a1af567baabfe06f90d62dac826fa51e4d50bf322e6712cbaf6bc6aabc4a757b`.
No reference change was needed.

For each column of height `h`, let `v1 ... vm` be its nonzero values in original
top-to-bottom order. The output column is `h-m` zeros followed by that exact
sequence. This determines a lawful output for every nonempty rectangular ARC
grid of dimensions `1..30` with integer colors `0..9`. Duplicate values remain
duplicated; columns never interact. Gray `5` is movable foreground, and zero is
background regardless of color frequencies. This is the Racket authority used
for actual labels. Python rival functions and the independent adjacent-swap
procedure are diagnostics.

## Domain and exact controls

The validator checks the rule's full ARC domain. An all-zero column has an empty
sequence; a full column already has no gaps; a singleton simply falls to the
bottom; an already-settled column is unchanged. Blank, solid, singleton,
one-row, one-column, and already-settled grids therefore remain accepted.
Malformed rectangles, booleans, nonintegers, out-of-range colors, and dimensions
outside `1..30` are rejected. Metadata cannot waive those checks.

The sampler deliberately uses narrower construction bounds. `grid_h=3..24`,
`grid_w=2..18`, `active_cols=1..18`, and `n_distinct_colors=1..9` are four exact
numeric controls, subject to width and occupied-capacity constraints. Requested
values are realized exactly or rejected as incompatible. They are not silently
clamped by difficulty. Unknown and previously ignored arguments fail; `None`
means unset. `palette_size` is one compatibility alias for the palette count,
and cannot claim independent variation. Matching aliases are accepted and
conflicting values are rejected.

`texture` is a diagnostic construction mode with `scattered`, `all_at_bottom`,
`single_value_columns`, and `no_cells`. These modes need not be uniquely
recoverable from an observed grid. `single_value_columns` means one nonzero
cell per active column. `no_cells` is incompatible with positive active-column
or palette-count requests. Exact overrides enter the diagnostic path and do
not inherit ordinary lesson guarantees.

Ordinary free draws keep at most five cells in each active column. The free
palette-capacity correction raises the required active-column count when
necessary and fills available positions without exceeding that cap. The cap
is a construction parameter: the rule itself has no five-cell capacity. Dense
and sparse teaching inputs both contain `h-1 >= 6` occupied cells in a column,
so ordinary lessons expose the difference.

## Why two teaching types and four demonstrations

Every teaching grid has height at least seven, width at least six, and a main
column with every row occupied except one internal gap. Its nonzero sequence
starts `a,b,a` and ends `a`, where `a != b`, with at least six values. It includes
gray `5`, an occupied bottom cell, and nonzero cells above the gap. These choices
make gray mobility, bottom participation, stable order, internal gap removal,
and more-than-five-cell capacity observable. The `a,b,a` sequence is neither
numerically sorted nor equal to its reversal. The occupied bottom prevents a
rigid column translation from removing the internal gap.

Dense teaching makes a nonzero color the unique mode. If `P` cells are occupied
and the palette has `k` colors, the dominant color occurs `P-(k-1)` times.
The chosen occupancy satisfies `2P > hw+k-1`, so it exceeds the number of zero
cells. This refutes treating the most frequent color as background.

The first ten-rival checks missed an interaction: apply a five-cell cap only
when zero is modal. In the earlier ordinary support, the long-column scenes
were also foreground-modal; the conditional rival therefore agreed everywhere.
The retained [interaction finding](checks/interaction-before/review_evidence.json)
and [actual Racket counterexample](checks/interaction-before/racket.json)
explain why the first green rival results were insufficient. The prior
10,080 boundary cases and 30,292 witness-grid diagnostics remain evidence for
that superseded source, not final-source reruns.

Sparse teaching removes the coupling. It occupies `P=h+w-2` cells while still
giving the main column `h-1 >= 6` cells. Because
`hw-2P=(h-2)(w-2)>0`, zero outnumbers all nonzero cells combined. Thus zero is
uniquely modal in a scene that requires preserving more than five values.
The conditional rival must delete a nonzero cell and is distinguishable.

The period-five ordinary cycle is
`dense_teaching, sparse_teaching, dense_teaching, sparse_teaching, free`.
Across a complete period, this is 80% teaching and 20% free. `EXAMPLES_NEEDED=4`
gives a five-pair bundle. Every five consecutive raw indices contain two dense
and two sparse teaching examples, so any single query holdout leaves at least
one of each type among the demonstrations. This replaces the earlier
three-demonstration design. The tests now require every declared rival to be
refuted by a remaining demonstration, including when the held-out query would
also agree with that rival.

The four canonical-fit shortcuts are `gray5_fixed_barrier`,
`bottom_five_capacity`, `modal_background`, and `zero_modal_cap`; all fit the
five supplied canonical pairs. Seven further lesson rivals cover ignoring the
bottom row, reversing order, sorting in both directions, rigid translation,
rightward compaction, and identity. There are eleven distinct rivals, with
repeated namespace entries in the receipts. The old ignore-bottom audit is a
sampler-only shortcut: it already disagrees with the canonical pairs.

## What the retained checks establish

| Final-source evidence | Result |
|---|---|
| [Battery](checks/after-v31/result.json) and [stage summary](checks/after-v31/checks/2a43e4f3a796_after_battery_summary.json) | 10/12 pass. `selfcheck` and `defect_lint` fail; the aggregate remains failed. Selected authority synchronization and execution parity pass. |
| [Portable task tests](checks/task-tests-isolated-v31/result.json) | 60 passed, zero failed/errors/skipped. The [initial stage](checks/task-tests-v31/result.json) failed prerequisite isolation because pytest was absent; it executed no tests. |
| [Actual Racket materializer census](checks/lesson-census-v31.json) | 300 lessons with four demonstrations and one query, 1,500 unique inputs, and 1,500 rotations; zero materialization/scoring errors or listed-rival ambiguity. |
| [Fixed-seed schedule census](checks/schedule-census-v31.json) | Seed zero, five starting residues across three bands: 15 materialized lessons, 75 pairs, 75 required rotations, and nine globally unique inputs; no listed-rival ambiguity. The bands coincide at this seed, so their unique counts must not be added. |
| [Required-rotation semantic check](checks/required-rotations-v31/result.json) | Passed, exit zero. Twelve materialized lessons and 60 required rotations have no ambiguity, hook warnings, or errors against the declared rivals. |
| [Final Racket witnesses](checks/final-witnesses/comparison.json) | Eighteen actual matches: 12 authored endpoint/counterexample inputs plus dense index 0 and sparse index 1 at seed zero in all three bands. All inputs pass the validator, and sparse samples refute the conditional cap. |
| [Independent Python probe](checks/distribution-v31.json) | 100 seeds, five starts, three bands: 1,500 complete windows and 7,500 rotations. Every one of the eleven distinct rivals is refuted on every rotation, with zero sample/rival errors. |
| [Final code review](checks/final-code-review.json) | Source/test/probe identities retained, no blocking findings, and six targeted conditional-witness cases passed. |

The [reusable probe](repo/generators/2a43e4f3a796/workspace/probe_distribution.py)
defaults to the selected source's positive integer `EXAMPLES_NEEDED`, falling
back to three only when absent or invalid; `--train` can set the count
explicitly. The final retained run pins `--train 4`. Its 1,500 marginal draws
exclude 1,200 additional inputs used to complete overlapping windows. It uses
Python adjacent-swap labels and direct generator calls, without materializer
filtering, deduplication, rejection, or Racket execution. The separate census
provides actual-materializer and Racket evidence. Neither population is a proof
of universal identifiability or exhaustive support. The raw-index schedule
argument does not by itself establish behavior under accepted-index filtering.
No universal `lesson_identifiable` hook is declared; the semantic reports use
the stated rival family as their assessment basis.

## Remaining actions

The battery's `selfcheck` failure counts 0/60 rejected mutations, including
blanking a grid, deleting a minority color, adding an in-range color, and
duplicating a row. Its `defect_lint` warnings similarly demand rejection of
lawful blank, singleton, solid, and short-line inputs. Stable compaction remains
defined on those grids. These are shared-tool false positives against this
task's documented total domain and need explicit tool review; the retained
failure statuses remain visible. The validator was not narrowed to manufacture
a green rejection rate. The final Racket witnesses include blank, singleton,
solid, settled, short-line, and small-grid examples that substantiate their
lawfulness.

The existing audit `review-0867d19380f40c97:v0001` remains `needs_triage` in
[the current task index](repo/generators/2a43e4f3a796/evidence/review_index.json).
The new construction and the final distribution/census evidence address its
occupied-bottom support concern. A maintainer must explicitly record any
resolution against final SHA-256
`6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9`
and those receipts. Source replacement, this documentation, and generic
acceptance do not automatically close it.

This work broadens and structures support for the stated rule without claiming
every lawful input is sampled or every possible rival is excluded. Approval
and training admission are not changed by these diagnostics. Current source
decisions live in [the task notes](repo/generators/2a43e4f3a796/notes.md);
historical evidence is retained through the links above rather than copied
into a cumulative review ledger.
